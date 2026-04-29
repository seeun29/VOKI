# cart.py

class Cart:
    def __init__(self, is_takeout: bool):
        self.is_takeout = is_takeout
        self.items = []

    def add_item(self, menu: dict, temperature: str, size: str, quantity: int, options: list, price: int):
        self.items.append({
            "menu": {
                "menu_id": menu["menu_id"],
                "menu_name": menu["menu_name"]
            },
            "temperature": temperature,
            "size": size,
            "quantity": quantity,
            "options": options,
            "total_price": price
        })

    def get_total(self) -> int:
        return sum(item["total_price"] for item in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0

    def summarize(self) -> str:
        lines = []
        for i, item in enumerate(self.items, 1):
            temp_str = "아이스" if item["temperature"] == "ICE" else "따뜻한" if item["temperature"] == "HOT" else ""
            option_str = ", ".join([o["name"] for o in item["options"]]) if item["options"] else "없음"
            lines.append(
                f"{i}. {item['menu']['menu_name']} {temp_str} {item['size']} "
                f"{item['quantity']}잔 / 옵션: {option_str} / {item['total_price']:,}원"
            )
        lines.append(f"\n💰 총 합계: {self.get_total():,}원")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "is_takeout": self.is_takeout,
            "items": self.items,
            "total_price": self.get_total()
        }

    def clear(self):
        self.items = []