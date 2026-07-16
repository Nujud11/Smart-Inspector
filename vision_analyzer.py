from __future__ import annotations

import base64
import io
import os
from typing import Literal

from dotenv import load_dotenv
from google import genai
from PIL import Image
from pydantic import BaseModel, Field


load_dotenv()


class VehicleEvidence(BaseModel):
    identifier: str = Field(
        description=(
            "Stable identifier such as vehicle_a or vehicle_b."
        )
    )

    color: str = Field(
        description="Main visible vehicle color."
    )

    vehicle_type: str = Field(
        description=(
            "Vehicle type such as sedan, SUV, pickup, "
            "truck, bus, or motorcycle."
        )
    )

    relative_position: Literal[
        "front",
        "behind",
        "left",
        "right",
        "inside_roundabout",
        "entering_roundabout",
        "unclear",
    ]

    visible_damage: Literal[
        "front",
        "rear",
        "left_side",
        "right_side",
        "multiple",
        "none",
        "unclear",
    ]

    motion_role: Literal[
        "travelling_straight",
        "likely_changing_lane",
        "inside_roundabout",
        "entering_roundabout",
        "reversing",
        "stationary",
        "unclear",
    ]

    damage_description: str = Field(
    description=(
        "وصف عربي مختصر وواضح للضرر الظاهر في المركبة. "
        "يجب أن تكون القيمة باللغة العربية فقط."
    )
)


class AccidentVisionAnalysis(BaseModel):
    vehicle_count: int

    vehicles: list[VehicleEvidence]

    road_type: Literal[
        "straight_road",
        "intersection",
        "roundabout",
        "parking_area",
        "unclear",
    ]

    likely_scenario: Literal[
        "rear_end_collision",
        "unsafe_lane_change",
        "failure_to_yield_roundabout",
        "side_collision",
        "reversing_collision",
        "unclear",
    ]

    visual_confidence: int = Field(
        ge=0,
        le=100,
    )

    sufficient_visual_evidence: bool

    visual_evidence: list[str] = Field(
        description=(
            "قائمة بالأدلة البصرية باللغة العربية فقط. "
            "كل عنصر يجب أن يكون جملة عربية واضحة."
        )
    )

    inconsistencies: list[str] = Field(
        description=(
            "قائمة بالتعارضات بين الصور باللغة العربية فقط."
        )
    )

    limitations: list[str] = Field(
        description=(
            "قائمة بقيود التحليل باللغة العربية فقط."
        )
    )

def prepare_image(image: Image.Image) -> str:
    """
    تصغير الصورة وتحويلها إلى Base64 لإرسالها إلى Gemini.
    """

    image = image.convert("RGB")

    # تقليل الحجم مع الحفاظ على نسبة الأبعاد
    image.thumbnail((1024, 1024))

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=72,
        optimize=True,
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


def analyze_accident_images(
    images: list[Image.Image],
) -> AccidentVisionAnalysis:
    """
    تحليل جميع صور الحادث معًا باستخدام Gemini Vision.
    """

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "لم يتم العثور على متغير البيئة GEMINI_API_KEY."
        )

    if not images:
        raise ValueError(
            "يجب إرسال صورة واحدة على الأقل."
        )

    client = genai.Client(api_key=api_key)

    prompt = """
أنت مكوّن استخراج الأدلة البصرية في نموذج أولي لتحليل
الحوادث المرورية.

الصور المرفوعة تمثل زوايا مختلفة للحادث نفسه.

حلل جميع الصور معًا، واستخرج فقط المعلومات التي يمكن
ملاحظتها بصريًا.

المطلوب:

1. تحديد عدد المركبات المختلفة.
2. إعطاء معرف ثابت لكل مركبة، مثل vehicle_a وvehicle_b.
3. تحديد لون كل مركبة ونوعها.
4. تحديد الموقع النسبي لكل مركبة.
5. تحديد موضع الضرر الظاهر ووصفه.
6. تحديد نوع الطريق.
7. تحديد النمط البصري الأكثر احتمالًا للحادث.
8. ذكر الأدلة التي تدعم النتيجة.
9. ذكر أي تعارض بين الصور.
10. ذكر القيود التي تمنع الوصول إلى استنتاج مؤكد.

الأنماط المدعومة:

- rear_end_collision
- unsafe_lane_change
- failure_to_yield_roundabout
- side_collision
- reversing_collision
- unclear

تعليمات صارمة:

- استخدم فقط المعلومات الظاهرة في الصور.
- لا تحدد المسؤولية القانونية أو نسب الخطأ.
- لا تفترض السرعة أو حالة الإشارة أو سلوك السائق.
- قارن بين ألوان المركبات وأنواعها واتجاهاتها والأضرار
  الظاهرة في جميع الصور.
- إذا اختلفت مواقع الضرر أو المركبات بين الصور، سجّل ذلك
  بوضوح ضمن inconsistencies.
- إذا لم تكن الأدلة كافية، استخدم unclear.
- إذا تعذر إجراء تحليل موثوق، اجعل
  sufficient_visual_evidence مساويًا لـ false.

لغة الإخراج:

- يجب أن تكون جميع النصوص الوصفية باللغة العربية فقط.
- يجب أن يكون damage_description باللغة العربية.
- يجب أن تكون عناصر visual_evidence باللغة العربية.
- يجب أن تكون عناصر inconsistencies باللغة العربية.
- يجب أن تكون عناصر limitations باللغة العربية.
- لا تستخدم اللغة الإنجليزية في أي جملة وصفية.
- احتفظ فقط بالقيم التصنيفية المحددة في الـSchema
  باللغة الإنجليزية، مثل front وrear وunclear، لأن النظام
  يستخدمها برمجيًا.
"""

    request_input: list[dict] = [
        {
            "type": "text",
            "text": prompt,
        }
    ]

    for image in images:
        request_input.append(
            {
                "type": "image",
                "data": prepare_image(image),
                "mime_type": "image/jpeg",
            }
        )

    print("[analysis] Gemini request started", flush=True)

    interaction = client.interactions.create(
        model="gemini-3.1-flash-lite",
        input=request_input,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": (
                AccidentVisionAnalysis.model_json_schema()
            ),
        },
    )

    print("[analysis] Gemini response received", flush=True)

    return AccidentVisionAnalysis.model_validate_json(
        interaction.output_text
    )