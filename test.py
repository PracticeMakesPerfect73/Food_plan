def get_recipe_word(count):
    count = abs(count) % 100
    if 11 <= count <= 19:
        return "рецептов"
    i = count % 10
    if i == 1:
        return "рецепт"
    if 2 <= i <= 4:
        return "рецепта"
    return "рецептов"


def test_get_recipe_word():
    print(f"{'Число':<6} | Склонение")
    print("-" * 22)
    for i in range(1, 151):
        word = get_recipe_word(i)
        print(f"{i:<6} | {word}")

        
if __name__ == "__main__":
    test_get_recipe_word()
