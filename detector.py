from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

import numpy as np
from PIL import Image
from ultralytics import YOLO


# COCO vehicle classes:
# 2 = car, 3 = motorcycle, 5 = bus, 7 = truck
VEHICLE_CLASS_IDS = [2, 3, 5, 7]

MIN_YOLO_CONFIDENCE = 0.35
MIN_VALIDATION_AVERAGE = 65.0


@lru_cache(maxsize=1)
def load_model() -> YOLO:
    """
    تحميل نموذج YOLO مرة واحدة فقط.
    """
    return YOLO("yolov8n.pt")


def detect_vehicles(
    image: Image.Image,
    confidence_threshold: float = MIN_YOLO_CONFIDENCE,
) -> dict[str, Any]:
    """
    تشغيل YOLO على صورة واحدة واكتشاف المركبات.
    """

    image = image.convert("RGB")
    model = load_model()

    results = model.predict(
        source=np.array(image),
        conf=confidence_threshold,
        classes=VEHICLE_CLASS_IDS,
        verbose=False,
    )

    result = results[0]
    detections: list[dict[str, Any]] = []

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

    # result.plot() يعيد الصورة بنظام BGR
    annotated_bgr = result.plot()
    annotated_rgb = annotated_bgr[:, :, ::-1]
    annotated_image = Image.fromarray(annotated_rgb)

    if detections:
        average_confidence = round(
            sum(item["confidence"] for item in detections)
            / len(detections),
            2,
        )
    else:
        average_confidence = 0.0

    return {
        "annotated_image": annotated_image,
        "detections": detections,
        "vehicle_count": len(detections),
        "average_confidence": average_confidence,
    }


def validate_accident_images(
    images: list[Image.Image],
) -> dict[str, Any]:
    """
    تشغيل YOLO على جميع الصور والتحقق من صلاحيتها قبل إرسالها إلى Gemini.

    شروط النجاح:
    - وجود مركبتين على الأقل في 75% من الصور.
    - متوسط الثقة العام لا يقل عن 65%.
    """

    if not images:
        return {
            "passed": False,
            "reason": "لم يتم رفع أي صور.",
            "results": [],
            "overall_confidence": 0.0,
            "valid_images": 0,
            "required_valid_images": 0,
        }

    detection_results = [
        detect_vehicles(image)
        for image in images
    ]

    valid_images = sum(
        result["vehicle_count"] >= 2
        for result in detection_results
    )

    required_valid_images = max(
        1,
        math.ceil(len(images) * 0.75),
    )

    image_confidences = [
        result["average_confidence"]
        for result in detection_results
        if result["vehicle_count"] > 0
    ]

    overall_confidence = (
        round(
            sum(image_confidences) / len(image_confidences),
            2,
        )
        if image_confidences
        else 0.0
    )

    enough_vehicles = valid_images >= required_valid_images
    confidence_is_good = (
        overall_confidence >= MIN_VALIDATION_AVERAGE
    )

    passed = enough_vehicles and confidence_is_good

    if not enough_vehicles:
        reason = (
            f"تم اكتشاف مركبتين بوضوح في {valid_images} صورة فقط، "
            f"بينما المطلوب {required_valid_images} صور على الأقل."
        )
    elif not confidence_is_good:
        reason = (
            f"متوسط ثقة YOLO هو {overall_confidence}%، "
            f"بينما الحد الأدنى المطلوب "
            f"{MIN_VALIDATION_AVERAGE}%."
        )
    else:
        reason = (
            "اجتازت الصور مرحلة التحقق، "
            "وأصبحت جاهزة للتحليل المتقدم."
        )

    return {
        "passed": passed,
        "reason": reason,
        "results": detection_results,
        "overall_confidence": overall_confidence,
        "valid_images": valid_images,
        "required_valid_images": required_valid_images,
    }