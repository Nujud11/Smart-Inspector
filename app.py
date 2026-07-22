from __future__ import annotations

import gc
import json
import os
import uuid
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from PIL import Image
from werkzeug.utils import secure_filename

from detector import validate_accident_images
from rules import apply_traffic_rules, calculate_final_confidence
from vision_analyzer import analyze_accident_images


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
RESULT_FOLDER = BASE_DIR / "static" / "results"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_IMAGES = 4

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RESULT_FOLDER.mkdir(parents=True, exist_ok=True)


app = Flask(__name__)

# تستخدمها Flask لرسائل النجاح والخطأ المؤقتة.
# غيّريها مستقبلًا عند نشر المشروع.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "smart-traffic-prototype-secret")

# حد إجمالي تقريبي للطلب المرفوع.
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    """التحقق من امتداد الصورة."""

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def save_uploaded_images(
    files: list[Any],
    case_id: str,
) -> tuple[list[Image.Image], list[str]]:
    """
    حفظ الصور وإرجاع:
    1. صور PIL المستخدمة في التحليل.
    2. روابط الصور المستخدمة في الواجهة.
    """

    case_folder = UPLOAD_FOLDER / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    pil_images: list[Image.Image] = []
    image_urls: list[str] = []

    for index, uploaded_file in enumerate(files, start=1):
        original_name = secure_filename(uploaded_file.filename)

        extension = original_name.rsplit(".", 1)[1].lower()
        filename = f"accident_{index}.{extension}"

        file_path = case_folder / filename
        uploaded_file.save(file_path)

        image = Image.open(file_path).convert("RGB")
        pil_images.append(image)

        image_urls.append(
            url_for(
                "static",
                filename=f"uploads/{case_id}/{filename}",
            )
        )

    return pil_images, image_urls


def save_yolo_results(
    detection_results: list[dict[str, Any]],
    case_id: str,
) -> list[dict[str, Any]]:
    """حفظ صور YOLO المعلّمة وتجهيز بيانات عرضها."""

    case_folder = RESULT_FOLDER / case_id
    case_folder.mkdir(parents=True, exist_ok=True)

    rendered_results: list[dict[str, Any]] = []

    for index, result in enumerate(detection_results, start=1):
        filename = f"yolo_{index}.jpg"
        file_path = case_folder / filename

        result["annotated_image"].save(
            file_path,
            format="JPEG",
            quality=90,
        )

        rendered_results.append(
            {
                "image_url": url_for(
                    "static",
                    filename=f"results/{case_id}/{filename}",
                ),
                "vehicle_count": result["vehicle_count"],
                "average_confidence": result["average_confidence"],
            }
        )

    return rendered_results


def translate_value(value: str) -> str:
    """ترجمة قيم Gemini الأساسية للعرض العربي."""

    translations = {
        "front": "في الأمام",
        "behind": "في الخلف",
        "left": "على اليسار",
        "right": "على اليمين",
        "rear": "في الخلف",
        "left_side": "الجانب الأيسر",
        "right_side": "الجانب الأيمن",
        "multiple": "عدة مواضع",
        "none": "لا يوجد ضرر ظاهر",
        "unclear": "غير واضح",
        "sedan": "سيدان",
        "suv": "مركبة رياضية",
        "pickup": "بيك أب",
        "truck": "شاحنة",
        "straight_road": "طريق مستقيم",
        "intersection": "تقاطع",
        "roundabout": "دوار",
        "parking_area": "مواقف",
        "rear_end_collision": "اصطدام خلفي",
        "unsafe_lane_change": "تغيير مسار غير آمن",
        "failure_to_yield_roundabout": "عدم إعطاء الأفضلية عند الدوار",
        "side_collision": "اصطدام جانبي",
        "reversing_collision": "اصطدام أثناء الرجوع",
        "travelling_straight": "تسير بصورة مستقيمة",
        "likely_changing_lane": "يُحتمل أنها تغير المسار",
        "inside_roundabout": "داخل الدوار",
        "entering_roundabout": "تدخل الدوار",
        "reversing": "ترجع إلى الخلف",
        "stationary": "متوقفة",
        "blue": "زرقاء",
        "red": "حمراء",
        "white": "بيضاء",
        "black": "سوداء",
        "silver": "فضية",
        "gray": "رمادية",
        "grey": "رمادية",
        "brown": "بنية",
        "orange": "برتقالية",
    }

    return translations.get(value.lower(), value)


@app.context_processor
def inject_helpers() -> dict[str, Any]:
    """جعل دالة الترجمة متاحة داخل ملفات HTML."""

    return {"translate_value": translate_value}


@app.get("/")
def index():
    """الصفحة الرئيسية."""

    return render_template("index.html")

@app.get("/about")
def about():
    """صفحة التعريف بالمنصة."""

    return render_template("about.html")


@app.get("/roadmap")
def roadmap():
    """صفحة الرؤية المستقبلية."""

    return render_template("roadmap.html")


@app.get("/pricing")
def pricing():
    """صفحة الباقات."""

    return render_template("pricing.html")

@app.get("/pricing")
def pricing():
    """صفحة الباقات."""

    return render_template("pricing.html")


@app.get("/team")
def team():
    """صفحة فريق المشروع."""

    students = [
        {
            "name": "اسم الطالب الأول",
            "city": "المدينة",
            "school": "اسم المدرسة الثانوية",
            "bio": "",
            "email": "",
        },
        {
            "name": "اسم الطالب الثاني",
            "city": "المدينة",
            "school": "اسم المدرسة الثانوية",
            "bio": "",
            "email": "",
        },
        {
            "name": "اسم الطالب الثالث",
            "city": "المدينة",
            "school": "اسم المدرسة الثانوية",
            "bio": "",
            "email": "",
        },
        {
            "name": "اسم الطالب الرابع",
            "city": "المدينة",
            "school": "اسم المدرسة الثانوية",
            "bio": "",
            "email": "",
        },
        {
            "name": "اسم الطالب الخامس",
            "city": "المدينة",
            "school": "اسم المدرسة الثانوية",
            "bio": "",
            "email": "",
        },
        {
            "name": "اسم الطالب السادس",
            "city": "المدينة",
            "school": "اسم المدرسة الثانوية",
            "bio": "",
            "email": "",
        },
    ]

    supervisors = [
        {
            "name": "د. مرتضى",
            "role": "مشرف مسار ميثاق الخوارزميات",
            "city": "",
            "organization": "برنامج مدن المستقبل 2026",
            "bio": "",
            "email": "",
        },
        {
            "name": "نجود العبيد",
            "role": "المطور التقني للمشروع",
            "city": "الأحساء",
            "organization": "المعاين الذكي",
            "bio": "",
            "email": "",
        },
    ]

    return render_template(
        "team.html",
        students=students,
        supervisors=supervisors,
    )


@app.get("/new-case")
def new_case():
    """صفحة رفع الصور."""

    return render_template("upload.html")


@app.get("/new-case")
def new_case():
    """صفحة رفع الصور."""

    return render_template("upload.html")


@app.post("/analyze")
def analyze():
    """استقبال الصور وتشغيل خط المعالجة كاملًا."""

    files = [
        file
        for file in request.files.getlist("accident_images")
        if file and file.filename
    ]

    if not files:
        flash("يرجى رفع صورة واحدة على الأقل.", "error")
        return redirect(url_for("new_case"))

    if len(files) > MAX_IMAGES:
        flash("يمكن رفع أربع صور كحد أقصى.", "error")
        return redirect(url_for("new_case"))

    invalid_files = [
        file.filename
        for file in files
        if not allowed_file(file.filename)
    ]

    if invalid_files:
        flash(
            "يسمح فقط بصور PNG وJPG وJPEG.",
            "error",
        )
        return redirect(url_for("new_case"))

    case_id = uuid.uuid4().hex[:10].upper()

    images: list[Image.Image] = []

    try:
        app.logger.info("Analysis started for case %s with %s image(s)", case_id, len(files))
        images, original_image_urls = save_uploaded_images(
            files,
            case_id,
        )

        # المرحلة الأولى: التحقق بواسطة YOLO.
        app.logger.info("YOLO started for case %s", case_id)
        yolo_validation = validate_accident_images(images)
        app.logger.info("YOLO finished for case %s", case_id)

        yolo_images = save_yolo_results(
            yolo_validation["results"],
            case_id,
        )

        if not yolo_validation["passed"]:
            return render_template(
                "result.html",
                case_id=case_id,
                status="validation_failed",
                original_images=original_image_urls,
                yolo_images=yolo_images,
                yolo=yolo_validation,
                vision=None,
                rule=None,
                final_confidence=None,
            )

        # المرحلة الثانية: استخراج الأدلة من Gemini.
        app.logger.info("Gemini started for case %s", case_id)
        vision_model = analyze_accident_images(images)
        app.logger.info("Gemini finished for case %s", case_id)
        vision_analysis = vision_model.model_dump()

        # المرحلة الثالثة: تطبيق القواعد المحلية.
        rule_result = apply_traffic_rules(vision_analysis)

        final_confidence = calculate_final_confidence(
            yolo_confidence=yolo_validation[
                "overall_confidence"
            ],
            gemini_confidence=vision_analysis[
                "visual_confidence"
            ],
            rule_confidence=rule_result[
                "rule_confidence"
            ],
        )

        return render_template(
            "result.html",
            case_id=case_id,
            status="completed",
            original_images=original_image_urls,
            yolo_images=yolo_images,
            yolo=yolo_validation,
            vision=vision_analysis,
            rule=rule_result,
            final_confidence=final_confidence,
        )

    except Exception as error:
        app.logger.exception("Accident analysis failed")

        return render_template(
            "result.html",
            case_id=case_id,
            status="error",
            error_message=str(error),
            original_images=[],
            yolo_images=[],
            yolo=None,
            vision=None,
            rule=None,
            final_confidence=None,
        )
    finally:
        for image in images:
            try:
                image.close()
            except Exception:
                pass
        gc.collect()


if __name__ == "__main__":
    app.run(debug=True)