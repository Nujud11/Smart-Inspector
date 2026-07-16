from __future__ import annotations

import gc
import math
import os
from functools import lru_cache
from typing import Any

import numpy as np
import torch
from PIL import Image, ImageDraw
from ultralytics import YOLO

# Keep CPU and memory use predictable on small Render instances.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
torch.set_num_threads(1)
try:
    torch.set_num_interop_threads(1)
except RuntimeError:
    pass

# COCO vehicle classes: car, motorcycle, bus, truck.
VEHICLE_CLASS_IDS = [2, 3, 5, 7]
MIN_YOLO_CONFIDENCE = 0.35
MIN_VALIDATION_AVERAGE = 65.0
MAX_INFERENCE_SIDE = 768
YOLO_IMAGE_SIZE = 320


@lru_cache(maxsize=1)
def load_model() -> YOLO:
    """Load the small YOLO model once per Gunicorn worker."""
    return YOLO("yolov8n.pt")


def detect_vehicles(
    image: Image.Image,
    confidence_threshold: float = MIN_YOLO_CONFIDENCE,
) -> dict[str, Any]:
    """Run low-memory CPU inference on one image."""
    working_image = image.convert("RGB")
    working_image.thumbnail((MAX_INFERENCE_SIDE, MAX_INFERENCE_SIDE))
    source_array = np.asarray(working_image)

    results = load_model().predict(
        source=source_array,
        conf=confidence_threshold,
        classes=VEHICLE_CLASS_IDS,
        device="cpu",
        imgsz=YOLO_IMAGE_SIZE,
        max_det=10,
        save=False,
        verbose=False,
    )

    result = results[0]
    detections: list[dict[str, Any]] = []
    annotated_image = working_image.copy()
    drawer = ImageDraw.Draw(annotated_image)

    if result.boxes is not None:
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            confidence = float(box.conf[0].item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append(
                {
                    "class_id": class_id,
                    "class_name": result.names[class_id],
                    "confidence": round(confidence * 100, 2),
                    "bounding_box": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                }
            )

            # Draw boxes without result.plot(), which consumes extra memory.
            drawer.rectangle((x1, y1, x2, y2), outline="red", width=3)
            label = f"{result.names[class_id]} {confidence:.0%}"
            drawer.text((x1 + 4, max(0, y1 + 4)), label, fill="red")

    average_confidence = (
        round(
            sum(item["confidence"] for item in detections)
            / len(detections),
            2,
        )
        if detections
        else 0.0
    )

    del drawer, source_array, results, result, working_image
    gc.collect()

    return {
        "annotated_image": annotated_image,
        "detections": detections,
        "vehicle_count": len(detections),
        "average_confidence": average_confidence,
    }


def validate_accident_images(images: list[Image.Image]) -> dict[str, Any]:
    """Validate accident images sequentially to limit peak memory."""
    if not images:
        return {
            "passed": False,
            "reason": "لم يتم رفع أي صور.",
            "results": [],
            "overall_confidence": 0.0,
            "valid_images": 0,
            "required_valid_images": 0,
        }

    detection_results: list[dict[str, Any]] = []
    for index, image in enumerate(images, start=1):
        print(f"[analysis] YOLO image {index}/{len(images)}", flush=True)
        detection_results.append(detect_vehicles(image))
        gc.collect()

    valid_images = sum(
        result["vehicle_count"] >= 2 for result in detection_results
    )
    required_valid_images = max(1, math.ceil(len(images) * 0.75))

    image_confidences = [
        result["average_confidence"]
        for result in detection_results
        if result["vehicle_count"] > 0
    ]
    overall_confidence = (
        round(sum(image_confidences) / len(image_confidences), 2)
        if image_confidences
        else 0.0
    )

    enough_vehicles = valid_images >= required_valid_images
    confidence_is_good = overall_confidence >= MIN_VALIDATION_AVERAGE
    passed = enough_vehicles and confidence_is_good

    if not enough_vehicles:
        reason = (
            f"تم اكتشاف مركبتين بوضوح في {valid_images} صورة فقط، "
            f"بينما المطلوب {required_valid_images} صور على الأقل."
        )
    elif not confidence_is_good:
        reason = (
            f"متوسط ثقة YOLO هو {overall_confidence}%، بينما الحد الأدنى "
            f"المطلوب {MIN_VALIDATION_AVERAGE}%."
        )
    else:
        reason = "اجتازت الصور مرحلة التحقق، وأصبحت جاهزة للتحليل المتقدم."

    return {
        "passed": passed,
        "reason": reason,
        "results": detection_results,
        "overall_confidence": overall_confidence,
        "valid_images": valid_images,
        "required_valid_images": required_valid_images,
    }
