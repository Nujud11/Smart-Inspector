from __future__ import annotations

from typing import Any


MIN_GEMINI_CONFIDENCE = 60
MIN_RULE_MATCH_SCORE = 60


# =========================================================
# أدوات مساعدة
# =========================================================

def normalize_text(value: Any) -> str:
    """
    تحويل أي قيمة إلى نص موحد لتسهيل البحث داخل
    الأوصاف والأدلة التي أعادها Gemini.
    """

    if value is None:
        return ""

    return str(value).strip().lower()


def get_vehicle_id(vehicle: dict[str, Any]) -> str:
    """
    إرجاع معرف المركبة بصورة آمنة.
    """

    return str(
        vehicle.get("identifier", "unknown_vehicle")
    )


def get_vehicle_damage_text(
    vehicle: dict[str, Any],
) -> str:
    """
    دمج نوع الضرر المنظم مع وصف الضرر النصي.

    مثال:
    visible_damage = multiple
    damage_description = أضرار في المصد الخلفي

    ينتج نصًا يمكن البحث فيه عن كلمة rear أو خلفي.
    """

    visible_damage = normalize_text(
        vehicle.get("visible_damage")
    )

    damage_description = normalize_text(
        vehicle.get("damage_description")
    )

    return f"{visible_damage} {damage_description}"


def collect_analysis_text(
    vision_analysis: dict[str, Any],
) -> str:
    """
    جمع الأدلة والوصف والقيود في نص واحد للبحث الدلالي البسيط.
    """

    text_parts: list[str] = []

    for key in (
        "visual_evidence",
        "inconsistencies",
        "limitations",
    ):
        values = vision_analysis.get(key, [])

        if isinstance(values, list):
            text_parts.extend(
                normalize_text(item)
                for item in values
            )

    for vehicle in vision_analysis.get("vehicles", []):
        text_parts.append(
            get_vehicle_damage_text(vehicle)
        )

    return " ".join(text_parts)


def contains_any(
    text: str,
    keywords: set[str],
) -> bool:
    """
    التحقق من وجود أي كلمة أو عبارة داخل النص.
    """

    normalized = normalize_text(text)

    return any(
        keyword in normalized
        for keyword in keywords
    )


def is_front_damage(
    vehicle: dict[str, Any],
) -> bool:
    """
    هل توجد أدلة على ضرر أمامي؟
    """

    visible_damage = normalize_text(
        vehicle.get("visible_damage")
    )

    damage_text = get_vehicle_damage_text(vehicle)

    if visible_damage == "front":
        return True

    front_keywords = {
        "front",
        "front bumper",
        "front right",
        "front left",
        "hood",
        "headlight",
        "مقدمة",
        "أمامي",
        "الأمامي",
        "الصدام الأمامي",
        "المصد الأمامي",
        "غطاء المحرك",
        "الكبوت",
    }

    return contains_any(
        damage_text,
        front_keywords,
    )


def is_rear_damage(
    vehicle: dict[str, Any],
) -> bool:
    """
    هل توجد أدلة على ضرر خلفي؟

    تقبل visible_damage = multiple إذا وصف Gemini
    ذكر المصد أو الجزء الخلفي.
    """

    visible_damage = normalize_text(
        vehicle.get("visible_damage")
    )

    damage_text = get_vehicle_damage_text(vehicle)

    if visible_damage == "rear":
        return True

    rear_keywords = {
        "rear",
        "rear bumper",
        "rear damage",
        "trunk",
        "back bumper",
        "مؤخرة",
        "خلفي",
        "الخلفي",
        "المصد الخلفي",
        "الصدام الخلفي",
        "الجهة الخلفية",
        "غطاء الصندوق",
        "صندوق السيارة",
    }

    return contains_any(
        damage_text,
        rear_keywords,
    )


def is_side_damage(
    vehicle: dict[str, Any],
) -> bool:
    """
    هل توجد أدلة على ضرر جانبي؟
    """

    visible_damage = normalize_text(
        vehicle.get("visible_damage")
    )

    damage_text = get_vehicle_damage_text(vehicle)

    if visible_damage in {
        "left_side",
        "right_side",
    }:
        return True

    side_keywords = {
        "left side",
        "right side",
        "side damage",
        "door",
        "quarter panel",
        "fender",
        "الجانب",
        "جانبي",
        "الباب",
        "الرفرف",
    }

    return contains_any(
        damage_text,
        side_keywords,
    )


def find_vehicle_by_position(
    vehicles: list[dict[str, Any]],
    position: str,
) -> dict[str, Any] | None:
    """
    البحث عن مركبة حسب موقعها النسبي فقط،
    بدون فرض نوع ضرر محدد.
    """

    for vehicle in vehicles:
        if (
            normalize_text(
                vehicle.get("relative_position")
            )
            == position
        ):
            return vehicle

    return None


def find_vehicle_by_motion(
    vehicles: list[dict[str, Any]],
    motion_role: str,
) -> dict[str, Any] | None:
    """
    البحث عن مركبة حسب حركة استنتجها Gemini.
    """

    for vehicle in vehicles:
        if (
            normalize_text(
                vehicle.get("motion_role")
            )
            == motion_role
        ):
            return vehicle

    return None


def has_serious_inconsistency(
    inconsistencies: list[str],
) -> bool:
    """
    رفض الحالة فقط عند وجود تعارض جوهري.

    لا نرفض الحالة بسبب قيود عامة مثل:
    - لا يمكن معرفة السرعة
    - الإضاءة ليلية
    - لا يمكن معرفة إن كانت المركبة متوقفة

    نرفض فقط عند تعارض واضح في هوية المركبات
    أو مواقع الضرر أو ترتيبها بين الصور.
    """

    if not inconsistencies:
        return False

    serious_keywords = {
        "different vehicles",
        "vehicle identity changes",
        "vehicle colors change",
        "contradictory damage",
        "damage changes between images",
        "positions are reversed",
        "vehicle order is reversed",
        "صور لحوادث مختلفة",
        "مركبات مختلفة",
        "اختلاف هوية المركبات",
        "اختلاف ألوان المركبات",
        "تعارض في موقع الضرر",
        "تغير موقع الضرر",
        "انعكاس ترتيب المركبات",
        "تبدل ترتيب المركبات",
        "الحوادث ليست نفسها",
    }

    combined = " ".join(
        normalize_text(item)
        for item in inconsistencies
    )

    return contains_any(
        combined,
        serious_keywords,
    )


def unclear_result(
    reason: str,
    *,
    rule_confidence: int = 50,
    evidence_points: list[str] | None = None,
) -> dict[str, Any]:
    """
    نتيجة تستخدم عندما لا تكفي الأدلة.
    """

    return {
        "matched": False,
        "rule_id": None,
        "scenario": "حالة غير واضحة",
        "scenario_code": "unclear",
        "vehicle_faults": {},
        "rule_confidence": rule_confidence,
        "rule_score": 0,
        "matched_evidence": evidence_points or [],
        "explanation": reason,
        "recommendation": (
            "طلب صور إضافية أو تحويل الحالة إلى مراجع بشري."
        ),
    }


# =========================================================
# قاعدة الاصطدام الخلفي بنظام النقاط
# =========================================================

def evaluate_rear_end_collision(
    vision_analysis: dict[str, Any],
) -> dict[str, Any] | None:
    """
    تقييم سيناريو الاصطدام الخلفي بنظام نقاط.

    لا يشترط تطابق جميع القيم حرفيًا.
    """

    vehicles = vision_analysis.get("vehicles", [])

    if len(vehicles) < 2:
        return None

    front_vehicle = find_vehicle_by_position(
        vehicles,
        "front",
    )

    rear_vehicle = find_vehicle_by_position(
        vehicles,
        "behind",
    )

    score = 0
    evidence: list[str] = []

    # وجود مركبة أمامية
    if front_vehicle:
        score += 15
        evidence.append(
            "تم تحديد مركبة في الموقع الأمامي."
        )

    # وجود مركبة خلفية
    if rear_vehicle:
        score += 15
        evidence.append(
            "تم تحديد مركبة في الموقع الخلفي."
        )

    # الضرر الخلفي في المركبة الأمامية
    if front_vehicle and is_rear_damage(front_vehicle):
        score += 25
        evidence.append(
            "ظهر ضرر خلفي في المركبة الأمامية."
        )

    # الضرر الأمامي في المركبة الخلفية
    if rear_vehicle and is_front_damage(rear_vehicle):
        score += 25
        evidence.append(
            "ظهر ضرر أمامي في المركبة الخلفية."
        )

    likely_scenario = normalize_text(
        vision_analysis.get("likely_scenario")
    )

    if likely_scenario == "rear_end_collision":
        score += 10
        evidence.append(
            "صنّف التحليل البصري النمط كاصطدام خلفي."
        )

    analysis_text = collect_analysis_text(
        vision_analysis
    )

    contact_keywords = {
        "rear-end",
        "rear end",
        "direct contact",
        "front bumper",
        "rear bumper",
        "اصطدام من الخلف",
        "اصطدام خلفي",
        "تلامس مباشر",
        "المصد الأمامي",
        "المصد الخلفي",
        "الصدام الأمامي",
        "الصدام الخلفي",
    }

    if contains_any(
        analysis_text,
        contact_keywords,
    ):
        score += 10
        evidence.append(
            "تضمنت الأدلة النصية وصفًا لتلامس أمامي-خلفي."
        )

    if score < MIN_RULE_MATCH_SCORE:
        return None

    if not front_vehicle or not rear_vehicle:
        return None

    # حماية الدرجة وإبقاؤها ضمن مقياس واضح من 100
    score = min(score, 100)

    # تحويل نقاط المطابقة إلى ثقة بين 70 و98
    rule_confidence = min(
        98,
        max(70, round(60 + score * 0.38)),
    )

    front_id = get_vehicle_id(front_vehicle)
    rear_id = get_vehicle_id(rear_vehicle)

    return {
        "matched": True,
        "rule_id": "REAR_END_001",
        "scenario": "اصطدام خلفي",
        "scenario_code": "rear_end_collision",
        "vehicle_faults": {
            front_id: 0,
            rear_id: 100,
        },
        "rule_confidence": rule_confidence,
        "rule_score": score,
        "matched_evidence": evidence,
        "explanation": (
            f"أظهرت الأدلة البصرية أن المركبة {rear_id} "
            f"كانت خلف المركبة {front_id}. كما ظهر ضرر "
            f"في مقدمة المركبة الخلفية وضرر في مؤخرة "
            f"المركبة الأمامية، مع وجود مؤشرات على تلامس "
            f"أمامي-خلفي بينهما. حققت الحالة {score} من "
            f"100 نقطة، ولذلك تمت مطابقة الأدلة مع قاعدة "
            f"الاصطدام الخلفي."
        ),
        "recommendation": (
            "النتيجة الأولية قابلة للمراجعة والاعتراض، "
            "ويجب اعتمادها من جهة مرورية مختصة."
        ),
    }


# =========================================================
# قاعدة تغيير المسار بنظام النقاط
# =========================================================

def evaluate_lane_change_collision(
    vision_analysis: dict[str, Any],
) -> dict[str, Any] | None:
    """
    تقييم تغيير المسار غير الآمن.
    """

    vehicles = vision_analysis.get("vehicles", [])

    changing_vehicle = find_vehicle_by_motion(
        vehicles,
        "likely_changing_lane",
    )

    straight_vehicle = find_vehicle_by_motion(
        vehicles,
        "travelling_straight",
    )

    if not changing_vehicle:
        return None

    score = 30
    evidence = [
        "تم تحديد مركبة في وضع يشير إلى تغيير المسار."
    ]

    if straight_vehicle:
        score += 15
        evidence.append(
            "تم تحديد مركبة أخرى تسير بصورة مستقيمة."
        )

    if is_side_damage(changing_vehicle):
        score += 20
        evidence.append(
            "ظهر ضرر جانبي في المركبة المغيّرة للمسار."
        )

    if (
        straight_vehicle
        and is_side_damage(straight_vehicle)
    ):
        score += 20
        evidence.append(
            "ظهر ضرر جانبي في المركبة المستقيمة."
        )

    if (
        normalize_text(
            vision_analysis.get("likely_scenario")
        )
        == "unsafe_lane_change"
    ):
        score += 15
        evidence.append(
            "صنّف التحليل البصري النمط كتغيير مسار."
        )

    if score < 65 or not straight_vehicle:
        return None

    score = min(score, 100)

    changing_id = get_vehicle_id(changing_vehicle)
    straight_id = get_vehicle_id(straight_vehicle)

    return {
        "matched": True,
        "rule_id": "LANE_CHANGE_001",
        "scenario": "تغيير مسار غير آمن",
        "scenario_code": "unsafe_lane_change",
        "vehicle_faults": {
            changing_id: 100,
            straight_id: 0,
        },
        "rule_confidence": min(
            92,
            max(70, round(55 + score * 0.35)),
        ),
        "rule_score": score,
        "matched_evidence": evidence,
        "explanation": (
            f"أظهر التحليل أن المركبة {changing_id} "
            f"كانت في وضع يشير إلى تغيير المسار، "
            f"بينما كانت المركبة {straight_id} تسير "
            f"بصورة مستقيمة، مع وجود أدلة ضرر جانبي. "
            f"حققت الحالة {score} من 100 نقطة في "
            f"قاعدة تغيير المسار."
        ),
        "recommendation": (
            "يفضل دعم النتيجة بفيديو أو بيانات إضافية "
            "لأن صور ما بعد الحادث قد لا تثبت حركة "
            "تغيير المسار بصورة قاطعة."
        ),
    }


# =========================================================
# قاعدة الدوار
# =========================================================

def evaluate_roundabout_collision(
    vision_analysis: dict[str, Any],
) -> dict[str, Any] | None:
    """
    تقييم الدخول إلى الدوار دون إعطاء الأفضلية.
    """

    vehicles = vision_analysis.get("vehicles", [])

    entering_vehicle = find_vehicle_by_position(
        vehicles,
        "entering_roundabout",
    )

    inside_vehicle = find_vehicle_by_position(
        vehicles,
        "inside_roundabout",
    )

    if not entering_vehicle or not inside_vehicle:
        return None

    entering_id = get_vehicle_id(entering_vehicle)
    inside_id = get_vehicle_id(inside_vehicle)

    return {
        "matched": True,
        "rule_id": "ROUNDABOUT_001",
        "scenario": "عدم إعطاء الأفضلية عند الدوار",
        "scenario_code": "failure_to_yield_roundabout",
        "vehicle_faults": {
            entering_id: 100,
            inside_id: 0,
        },
        "rule_confidence": 85,
        "rule_score": 80,
        "matched_evidence": [
            "تم تحديد مركبة تدخل الدوار.",
            "تم تحديد مركبة أخرى موجودة داخل الدوار.",
        ],
        "explanation": (
            f"أظهر التحليل أن المركبة {entering_id} "
            f"كانت تدخل الدوار، بينما كانت المركبة "
            f"{inside_id} موجودة داخله، ولذلك تمت "
            f"مطابقة قاعدة أولوية المركبة داخل الدوار."
        ),
        "recommendation": (
            "تعد النتيجة تجريبية، ويجب اعتماد القاعدة "
            "ونسب المسؤولية من جهة مرورية مختصة."
        ),
    }


# =========================================================
# تشغيل محرك القواعد
# =========================================================

def apply_traffic_rules(
    vision_analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    تطبيق القواعد على الحقائق التي استخرجها Gemini.

    القواعد مرتبة من الأكثر وضوحًا بصريًا إلى الأقل:
    1. اصطدام خلفي
    2. تغيير مسار
    3. دوار
    """

    visual_confidence = int(
        vision_analysis.get(
            "visual_confidence",
            0,
        )
        or 0
    )

    sufficient_evidence = vision_analysis.get(
        "sufficient_visual_evidence",
        False,
    )

    inconsistencies = vision_analysis.get(
        "inconsistencies",
        [],
    )

    vehicles = vision_analysis.get(
        "vehicles",
        [],
    )

    if len(vehicles) < 2:
        return unclear_result(
            "لم يتمكن التحليل من تحديد مركبتين "
            "بصورة كافية."
        )

    if visual_confidence < MIN_GEMINI_CONFIDENCE:
        return unclear_result(
            f"ثقة التحليل البصري هي "
            f"{visual_confidence}%، وهي أقل من الحد "
            f"التجريبي المطلوب "
            f"{MIN_GEMINI_CONFIDENCE}%."
        )

    # لا نرفض بسبب أي قيد بسيط.
    # نرفض فقط عند وجود تعارض جوهري.
    if has_serious_inconsistency(inconsistencies):
        return unclear_result(
            "اكتشف النظام تعارضًا جوهريًا بين الصور "
            "في هوية المركبات أو ترتيبها أو مواقع الضرر، "
            "ولذلك تحتاج الحالة إلى مراجعة بشرية.",
            rule_confidence=45,
        )

    # حتى لو Gemini كتب sufficient_visual_evidence=False،
    # نحاول مطابقة قاعدة قوية إذا كانت الأدلة المنظمة
    # متوفرة، بدل الرفض المباشر.
    candidate_results = [
        evaluate_rear_end_collision(
            vision_analysis
        ),
        evaluate_lane_change_collision(
            vision_analysis
        ),
        evaluate_roundabout_collision(
            vision_analysis
        ),
    ]

    matched_results = [
        result
        for result in candidate_results
        if result is not None
    ]

    if matched_results:
        # اختيار القاعدة التي حققت أعلى نقاط
        best_result = max(
            matched_results,
            key=lambda item: item.get(
                "rule_score",
                0,
            ),
        )

        # خفض بسيط في الثقة إذا اعتبر Gemini
        # الأدلة غير كافية، لكن لا نلغي النتيجة.
        if not sufficient_evidence:
            best_result["rule_confidence"] = max(
                65,
                best_result["rule_confidence"] - 10,
            )

            best_result["recommendation"] = (
                best_result["recommendation"]
                + " أشار التحليل البصري إلى وجود بعض "
                "القيود، لذلك يوصى بمراجعة النتيجة."
            )

        return best_result

    return unclear_result(
        "استخرج النظام معلومات عن المركبات والأضرار، "
        "لكن مجموع الأدلة لم يصل إلى الحد المطلوب "
        "لمطابقة أحد السيناريوهات الحالية."
    )


# =========================================================
# الثقة النهائية
# =========================================================

def calculate_final_confidence(
    yolo_confidence: float,
    gemini_confidence: float,
    rule_confidence: float,
) -> int:
    """
    حساب ثقة نهائية تجريبية من المكونات الثلاثة.

    YOLO أقل وزنًا لأنه يتحقق من وجود المركبات فقط،
    بينما Gemini والقواعد أكثر تأثيرًا في السيناريو.
    """

    final_score = (
        float(yolo_confidence) * 0.20
        + float(gemini_confidence) * 0.40
        + float(rule_confidence) * 0.40
    )

    return max(
        0,
        min(100, round(final_score)),
    )