import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 메뉴 전체 로드
def load_all_menus():
    menus = []
    for filename in ["menu_coffee.json", "menu_decaf.json", "menu_drink.json", "menu_tea.json"]:
        with open(filename, "r", encoding="utf-8") as f:
            menus.extend(json.load(f))
    return menus

with open("options.json", "r", encoding="utf-8") as f:
    OPTIONS = json.load(f)

MENU = load_all_menus()

# 발화 → 메뉴 매핑
def parse_order(user_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""
너는 투썸플레이스 키오스크 주문 파싱 AI야.
주로 고령자가 사용하므로 표현이 불명확하거나 메뉴명을 정확히 모를 수 있어.
사용자의 자연어 발화를 아래 메뉴에 매핑해서 JSON으로만 반환해.

메뉴 목록:
{json.dumps(MENU, ensure_ascii=False, indent=2)}

[온도 매핑]
ICE: "차가운", "시원한", "차게", "아이스", "냉커피", "얼음 넣어서", "차갑게"
HOT: "따뜻한", "뜨거운", "뜨끈한", "핫", "따뜻하게", "뜨겁게"
언급 없으면 → temperature: null

[사이즈 매핑]
R: "작은 거", "조그만 거", "작게", "레귤러", "기본", "R사이즈"
L: "큰 거", "라지", "크게", "L사이즈"
M: "제일 큰 거", "맥스", "엄청 크게"
언급 없으면 → size: null (기본 사이즈는 서버가 처리)

[수량 매핑]
"하나", "한 잔", "한 개" → 1
"둘", "두 잔", "두 개" → 2
언급 없으면 → quantity: 1

[메뉴 못 찾을 때]
메뉴명을 모르고 특징으로 설명하는 경우:
- "달달한 커피" → 바닐라라떼, 카라멜마끼아또 등 추천 1개 매핑
- "쓰지 않은 커피" → 바닐라라떼, 카페라떼 등 추천 1개 매핑
- "초코 들어간 거" → 카페모카, 초콜릿라떼 등 추천 1개 매핑
- "녹차 맛" → 그린티라떼, 말차크림라떼 매핑
- "그냥 커피", "아무거나" → 아메리카노 기본 추천
- 아무리 해도 매핑 불가 → {{"error": "없는 메뉴"}}

[주의사항]
- 존댓말/반말 구분 없이 의도만 파악
- 맞춤법 틀려도 발음 기준으로 파악 (예: "카라멜마끼야또" → 카라멜마끼아또)
- 흐릿하게 말해도 최대한 가까운 메뉴로 매핑 시도
- 절대 JSON 외 텍스트 반환 금지

반환 형식 (JSON만, 설명 없이):
{{"menu_id": 1, "menu_name": "아메리카노", "temperature": "ICE", "size": "R", "quantity": 1}}
"""
            },
            {"role": "user", "content": user_text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


# 발화 → 옵션
def parse_option(user_text: str, menu_category: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"""
너는 투썸플레이스 퍼스널 옵션 파싱 AI야.
주로 고령자가 사용하므로 표현이 불명확하거나 추가 옵션을 정확히 모를 수 있어.
사용자의 발화에서 추가 옵션을 파악해서 JSON으로만 반환해.

사용 가능한 옵션 목록:
{json.dumps(OPTIONS, ensure_ascii=False, indent=2)}

현재 메뉴 카테고리: {menu_category}

[샷 추가 - shot_add]
"진하게", "커피 맛 강하게", "샷 하나 더", "샷 추가", "쓰게 해줘", "커피 많이 넣어줘", "강하게 해줘"
→ shot_add: 1

[샷 연하게 - shot_weak]
"연하게", "약하게", "커피 적게", "연한 거로", "맛 약하게", "커피 맛 좀 줄여줘"
→ shot_weak

[시럽 - syrup_vanilla / syrup_hazelnut / syrup_caramel]
"바닐라 시럽", "바닐라 향 넣어줘" → syrup_vanilla
"헤이즐넛", "고소한 시럽" → syrup_hazelnut
"카라멜 시럽", "카라멜 넣어줘", "달달하게", "더 달게 시럽으로" → syrup_caramel

[휘핑크림 - whipping]
"휘핑 추가", "크림 올려줘", "위에 하얀 거 올려줘", "크림 얹어줘", "하얀 크림", "생크림 올려줘"
→ whipping

[물 조절 - water_amount]
"물 많이", "물 많이 넣어줘", "물 많이 타줘" → 많이
"물 보통", "물 적당히" → 보통
"물 적게", "물 조금만", "물 별로 없이" → 적게
"물 빼고", "물 없이", "물 넣지 마" → 없이(빼고)

[얼음량 - ice_amount]
"얼음 많이", "얼음 가득", "얼음 많이 넣어줘" → 많이
"얼음 보통", "얼음 적당히" → 보통
"얼음 조금만", "얼음 별로 없이", "얼음 적게" → 적게
"얼음 빼고", "얼음 없이", "얼음 넣지 마" → 없이(빼고)

[버블 - bubble]
"버블 추가", "타피오카 넣어줘", "펄 추가", "쫄깃한 거 넣어줘",
→ bubble

[우유 변경 - milk_*]
"두유로", "콩으로 해줘", "우유 말고 콩으로", "두유 우유" → milk_soy
"저지방 우유", "저지방으로" → milk_low_fat
"무지방 우유", "무지방으로", "살 안 찌는 우유" → milk_no_fat
"락토프리", "유당 없는 우유", "배 안 아픈 우유" → milk_lactofree
"오트로", "귀리 우유", "식물성으로", "오트밀크" → milk_oat

[드리즐 - drizzle_caramel / drizzle_chocolate]
"카라멜 드리즐", "카라멜 뿌려줘", "위에 카라멜" → drizzle_caramel
"초코 드리즐", "위에 초코 올려줘", "위에 초코 뿌려줘", "초콜릿 올려줘" → drizzle_chocolate

[당도 조절 - sweetness]
"더 달게", "달게 해줘", "설탕 더 넣어줘", "단 거 좋아" → 더 달게
"당도 보통", "보통 해줘" → 당도 보통
"덜 달게", "너무 달지 않게", "설탕 좀 빼줘", "달지 않게", "당 조금만", "당 줄여줘" → 덜 달게

[거품량 - foam_amount]
"거품 많이", "거품 가득" → 많이
"거품 보통" → 보통
"거품 조금", "거품 적게" → 적게
"거품 없이", "거품 빼줘", "거품 넣지 마" → 없이

[건너뛰기]
"그냥 줘", "됐어", "없어", "아니", "괜찮아", "기본으로",
"그냥 주세요", "추가 없이", "그대로 줘"
→ skip: true

[주의사항]
- 해당 카테고리에 applicable한 옵션만 처리
- 여러 옵션 동시 파악 가능 (예: "얼음 적게, 덜 달게" → 두 옵션 모두 반환)
- 맞춤법 틀려도 발음 기준으로 파악
- 절대 JSON 외 텍스트 반환 금지

반환 형식 (JSON만):
{{
  "skip": false,
  "options": [
    {{"key": "shot_add", "name": "에스프레소 샷 추가", "value": 1, "price": 800}},
    {{"key": "sweetness", "name": "당도 조절", "value": "덜 달게", "price": 0}}
  ]
}}
"""
            },
            {"role": "user", "content": user_text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# 발화 → 메뉴/옵션 질문
def explain_option(user_text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
너는 투썸플레이스 키오스크 안내 AI야.
고령자가 이해하기 쉽게 메뉴나 옵션을 설명해줘.
2~3문장으로 짧고 친절하게, 어려운 말 없이 쉽게 설명해.
가격이 있으면 같이 알려줘.
"""
            },
            {"role": "user", "content": user_text}
        ]
    )
    return response.choices[0].message.content


# 발화 → 의도 파악 
def parse_intent(user_text: str) -> dict:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
너는 사용자 발화의 의도를 파악하는 AI야.
아래 중 하나로만 분류해서 JSON으로 반환해.

의도 종류:
- "yes": 확인, 동의 ("네", "맞아", "응", "어", "좋아", "그래")
- "no": 거절, 취소 ("아니야", "아니", "싫어", "틀려", "다시")
- "skip": 옵션 건너뛰기 ("그냥 줘", "됐어", "없어", "기본으로")
- "takeout": 포장 ("포장", "가져갈게", "테이크아웃")
- "eat_in": - "eat_in": 매장 ("먹고 갈게요", "여기서 먹을게요", "매장", "여기서 먹어", "먹고가")
- "question": 질문 ("뭐야", "어떤 거야", "설명해줘", "뭐가 들어가", "어떤 맛이야", "얼마야")
- "unknown": 위에 해당 없음

반환 형식:
{"intent": "yes"}
"""
            },
            {"role": "user", "content": user_text}
        ],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


# 전체 대화 시뮬레이션 테스트
if __name__ == "__main__":
    print("=" * 50)
    print("테스트 1: 메뉴 매핑")
    tests = [
        "커피우유 차가운 걸로 하나",
        "아아 두 잔 줘봐요",
        "녹차티 따뜻하게 라지로",
        "딸기주스 주세요"  # 없는 메뉴
    ]
    for t in tests:
        result = parse_order(t)
        print(f"입력: {t}")
        print(f"결과: {result}\n")

    print("=" * 50)
    print("테스트 2: 옵션")
    option_tests = [
        ("덜 달게 해줘", "커피"),
        ("샷 추가하고 휘핑도 올려줘", "커피"),
        ("그냥 줘", "커피"),
        ("얼음 적게요", "음료"),
    ]
    for text, category in option_tests:
        result = parse_option(text, category)
        print(f"입력: {text} (카테고리: {category})")
        print(f"결과: {result}\n")

    print("=" * 50)
    print("테스트 3: 의도 파악")
    intent_tests = ["네 맞아요", "아니요", "그냥 줘", "포장해 주세요", "여기서 먹을게요"]
    for t in intent_tests:
        result = parse_intent(t)
        print(f"입력: {t} → {result}")