from llm import parse_order, parse_option, parse_intent, explain_option, MENU
from cart import Cart
import json

def get_menu_by_id(menu_id: int) -> dict:
    for m in MENU:
        if m["id"] == menu_id:
            return m
    return None

def voki_say(text: str):
    print(f"\n🤖 VOKI: {text}")

def user_input() -> str:
    return input(f"\n👤 사용자 입력 > ").strip()


# 메뉴 1개 주문 흐름
def order_one_menu() -> dict:
    item = {
        "menu": None,
        "temperature": None,
        "size": None,
        "quantity": 1,
        "options": [],
        "total_price": 0
    }

    # 메뉴 선택
    while True:
        result = parse_order(user_input())

        if "error" in result:
            voki_say("죄송해요, 해당 메뉴를 찾지 못했어요. 다시 말씀해주시겠어요?")
            continue

        menu_info = get_menu_by_id(result["menu_id"])
        item["menu"] = result
        item["temperature"] = result.get("temperature")
        item["size"] = result.get("size") or menu_info["default_size"]
        item["quantity"] = result.get("quantity", 1)

        temp_str = "아이스" if item["temperature"] == "ICE" else "따뜻한" if item["temperature"] == "HOT" else ""
        voki_say(f"{result['menu_name']} {temp_str} {item['size']} {item['quantity']}잔, 맞으시나요?")

        if parse_intent(user_input())["intent"] == "yes":
            break
        else:
            voki_say("다시 말씀해주세요. 어떤 메뉴로 하시겠어요?")

    # 퍼스널 옵션
    voki_say("샷 추가, 당도 조절 등 추가 옵션을 선택하시겠습니까?")
    user_text = user_input()
    intent = parse_intent(user_text)

    if intent["intent"] not in ["skip", "no"]:
        menu_category = menu_info.get("category", "커피")
        option_result = parse_option(user_text, menu_category)

        if not option_result.get("skip"):
            selected = option_result.get("options", [])
            if selected:
                item["options"] = selected
                option_names = ", ".join([
                    o["name"] + (f' ({o["value"]})' if o.get("value") else "")
                    for o in selected
                ])
                voki_say(f"{option_names} 추가되었습니다. 추가로 원하시는 옵션이 있으신가요?")

                while True:
                    user_text = user_input()
                    intent = parse_intent(user_text)

                    if intent["intent"] == "question":
                        voki_say(explain_option(user_text))
                        continue
                    if intent["intent"] in ["skip", "no"]:
                        break

                    more = parse_option(user_text, menu_category)
                    if more.get("skip") or not more.get("options"):
                        break
                    item["options"].extend(more["options"])
                    added = ", ".join([o["name"] for o in more["options"]])
                    voki_say(f"{added} 추가되었습니다. 추가로 원하시는 옵션이 있으신가요?")

    # 가격 계산
    base_price = menu_info["price"].get(item["size"], 0) * item["quantity"]
    option_price = sum(o.get("price", 0) for o in item["options"])
    item["total_price"] = base_price + option_price

    return item


# 메인 파이프라인
def run_pipeline():
    print("VOKI 주문 시뮬레이터 (텍스트 모드)")

    # Step 1. 매장/포장
    voki_say("안녕하세요! 드시고 가시나요?")
    intent = parse_intent(user_input())

    if intent["intent"] in ["eat_in", "yes"]:
        is_takeout = False
        voki_say("매장에서 드시는군요. 주문하실 메뉴를 말씀해주세요.")
    elif intent["intent"] in ["no", "takeout"]:
        is_takeout = True
        voki_say("포장이시군요. 주문하실 메뉴를 말씀해주세요.")
    else:
        voki_say("죄송해요, 드시고 가시나요, 포장이신가요?")
        intent = parse_intent(user_input())
        if intent["intent"] in ["eat_in", "yes"]:
            is_takeout = False
            voki_say("매장에서 드시는군요. 주문하실 메뉴를 말씀해주세요.")
        else:
            is_takeout = True
            voki_say("포장이시군요. 주문하실 메뉴를 말씀해주세요.")

    cart = Cart(is_takeout=is_takeout)

    # Step 2. 장바구니 루프
    while True:
        item = order_one_menu()
        cart.add_item(
            menu=item["menu"],
            temperature=item["temperature"],
            size=item["size"],
            quantity=item["quantity"],
            options=item["options"],
            price=item["total_price"]
        )

        temp_str = "아이스" if item["temperature"] == "ICE" else "따뜻한" if item["temperature"] == "HOT" else ""
        voki_say(
            f"{item['menu']['menu_name']} {temp_str} {item['size']} {item['quantity']}잔 "
            f"장바구니에 담았습니다. 추가로 주문하실 메뉴가 있으신가요?"
        )

        intent = parse_intent(user_input())
        if intent["intent"] in ["yes"]:
            voki_say("네! 추가 주문하실 메뉴를 말씀해주세요.")
        else:
            break

    # Step 3. 최종 확인
    takeout_str = "포장" if is_takeout else "매장"
    voki_say(f"주문 내역을 확인해드릴게요.\n\n{cart.summarize()}\n\n{takeout_str}으로 준비할까요?")

    if parse_intent(user_input())["intent"] == "yes":
        voki_say("결제를 진행할게요. 카드를 IC칩이 앞쪽을 향하도록 꽂아주세요.")
        voki_say(f"결제 완료! 총 {cart.get_total():,}원 결제되었습니다. 감사합니다 😊")
    else:
        voki_say("주문을 처음부터 다시 시작할게요.")
        run_pipeline()
        return

    print("\n" + "="*50)
    print("📋 최종 주문 구조화 결과:")
    print(json.dumps(cart.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    run_pipeline()