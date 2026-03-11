import anthropic
import json
import os

MEMORY_FILE = "memory.json"

def save_preferences(diet, allergies, cuisine, calories):
    memory = {
        "diet": diet,
        "allergies": allergies,
        "cuisine": cuisine,
        "calories": calories
    }
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)
    print("✅ Preferences saved for next time!")

def load_preferences():
    if not os.path.exists(MEMORY_FILE):
        return None
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

client = anthropic.Anthropic()

def get_preferences():
    print("\n🍽️  Welcome to the Meal Plan Agent!")

    # Check for saved preferences
    saved = load_preferences()
    if saved:
        print("\n📝 Found your saved preferences:")
        print(f"  Dietary restrictions: {saved['diet'] or 'none'}")
        print(f"  Allergies:            {saved['allergies'] or 'none'}")
        print(f"  Favorite cuisines:    {saved['cuisine'] or 'none'}")
        print(f"  Daily calorie goal:   {saved['calories'] or 'not specified'}")
        use_saved = input("\nUse these? (y/n): ").strip().lower()
        if use_saved == "y":
            return saved['diet'], saved['allergies'], saved['cuisine'], saved['calories']

    # Otherwise ask fresh
    print("\nAnswer a few quick questions to get started.\n")
    diet = input("Any dietary restrictions? (e.g. vegetarian, gluten-free, or press Enter to skip): ")
    allergies = input("Any allergies? (e.g. nuts, dairy, or press Enter to skip): ")
    cuisine = input("Favorite cuisines? (e.g. Italian, Mexican, or press Enter to skip): ")
    calories = input("Daily calorie goal? (e.g. 2000, or press Enter to skip): ")

    # Save for next time
    save_preferences(diet, allergies, cuisine, calories)

    return diet, allergies, cuisine, calories

def planner_agent(diet, allergies, cuisine, calories):
    print("\n⏳ Planning your week of meals...")

    prompt = f"""
    Create a 7-day meal plan based on these preferences:
    - Dietary restrictions: {diet or 'none'}
    - Allergies: {allergies or 'none'}
    - Preferred cuisines: {cuisine or 'any'}
    - Daily calorie goal: {calories or 'not specified'}

    Respond ONLY with a JSON object in this exact format, no other text:
    {{
        "monday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}},
        "tuesday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}},
        "wednesday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}},
        "thursday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}},
        "friday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}},
        "saturday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}},
        "sunday": {{"breakfast": "meal name", "lunch": "meal name", "dinner": "meal name"}}
    }}
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    meal_plan = json.loads(response.content[0].text)
    return meal_plan

def print_meal_plan(meal_plan):
    print("\n📅 Your 7-Day Meal Plan:")
    print("=" * 40)
    for day, meals in meal_plan.items():
        print(f"\n{day.upper()}")
        print(f"  Breakfast: {meals['breakfast']}")
        print(f"  Lunch:     {meals['lunch']}")
        print(f"  Dinner:    {meals['dinner']}")


def recipe_agent(meal_plan):
    print("\n⏳ Fetching recipes for each meal...")
    all_recipes = {}

    for day, meals in meal_plan.items():
        all_recipes[day] = {}
        for meal_type, meal_name in meals.items():
            print(f"  Getting recipe for {meal_name}...")

            prompt = f"""
            Give me a recipe for: {meal_name}

            Respond ONLY with a JSON object in this exact format, no other text:
            {{
                "ingredients": ["ingredient 1", "ingredient 2"],
                "instructions": ["step 1", "step 2"],
                "calories": 500
            }}
            """

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            recipe = json.loads(response.content[0].text)
            all_recipes[day][meal_type] = {
                "name": meal_name,
                "recipe": recipe
            }

    return all_recipes

def print_recipes(all_recipes):
    print("\n📖 Recipes:")
    print("=" * 40)
    for day, meals in all_recipes.items():
        print(f"\n{day.upper()}")
        for meal_type, details in meals.items():
            print(f"\n  {meal_type.upper()}: {details['name']}")
            print(f"  Calories: {details['recipe']['calories']} kcal")
            print(f"  Ingredients:")
            for ingredient in details['recipe']['ingredients']:
                print(f"    - {ingredient}")
            print(f"  Instructions:")
            for i, step in enumerate(details['recipe']['instructions'], 1):
                print(f"    {i}. {step}")

def shopper_agent(all_recipes):
    print("\n⏳ Generating your shopping list...")

    all_ingredients = []
    for day, meals in all_recipes.items():
        for meal_type, details in meals.items():
            all_ingredients.extend(details['recipe']['ingredients'])

    prompt = f"""
    Here is a list of ingredients from a 7-day meal plan:
    {json.dumps(all_ingredients)}

    Please consolidate this into a clean grocery shopping list.
    Combine duplicates, merge similar items, and organize by category.

    Respond ONLY with a JSON object in this exact format, no other text:
    {{
        "produce": ["item 1", "item 2"],
        "dairy": ["item 1", "item 2"],
        "pantry": ["item 1", "item 2"],
        "grains": ["item 1", "item 2"],
        "protein": ["item 1", "item 2"],
        "spices": ["item 1", "item 2"],
        "other": ["item 1", "item 2"]
    }}
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    shopping_list = json.loads(response.content[0].text)
    return shopping_list

def print_shopping_list(shopping_list):
    print("\n🛒 Your Grocery Shopping List:")
    print("=" * 40)
    for category, items in shopping_list.items():
        if items:
            print(f"\n{category.upper()}")
            for item in items:
                print(f"  □ {item}")



def save_to_file(meal_plan, all_recipes, shopping_list):
    filename = "meal_plan.txt"
    with open(filename, "w") as f:

        # Meal Plan
        f.write("7-DAY MEAL PLAN\n")
        f.write("=" * 40 + "\n")
        for day, meals in meal_plan.items():
            f.write(f"\n{day.upper()}\n")
            f.write(f"  Breakfast: {meals['breakfast']}\n")
            f.write(f"  Lunch:     {meals['lunch']}\n")
            f.write(f"  Dinner:    {meals['dinner']}\n")

        # Recipes
        f.write("\n\nRECIPES\n")
        f.write("=" * 40 + "\n")
        for day, meals in all_recipes.items():
            f.write(f"\n{day.upper()}\n")
            for meal_type, details in meals.items():
                f.write(f"\n  {meal_type.upper()}: {details['name']}\n")
                f.write(f"  Calories: {details['recipe']['calories']} kcal\n")
                f.write(f"  Ingredients:\n")
                for ingredient in details['recipe']['ingredients']:
                    f.write(f"    - {ingredient}\n")
                f.write(f"  Instructions:\n")
                for i, step in enumerate(details['recipe']['instructions'], 1):
                    f.write(f"    {i}. {step}\n")

        # Shopping List
        f.write("\n\nGROCERY SHOPPING LIST\n")
        f.write("=" * 40 + "\n")
        for category, items in shopping_list.items():
            if items:
                f.write(f"\n{category.upper()}\n")
                for item in items:
                    f.write(f"  □ {item}\n")

    print(f"\n✅ All done! Your meal plan has been saved to: {filename}")
    print(f"   Find it in your meal-plan-agent folder.")

# --- Run the agent ---
diet, allergies, cuisine, calories = get_preferences()
meal_plan = planner_agent(diet, allergies, cuisine, calories)
print_meal_plan(meal_plan)
all_recipes = recipe_agent(meal_plan)
print_recipes(all_recipes)
shopping_list = shopper_agent(all_recipes)
print_shopping_list(shopping_list)
save_to_file(meal_plan, all_recipes, shopping_list)

