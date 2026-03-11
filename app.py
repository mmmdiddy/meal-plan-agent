from flask import Flask, render_template, request, jsonify, session
import anthropic
import json
import os

app = Flask(__name__)
app.secret_key = "meal-plan-secret-key"

MEMORY_FILE = "memory.json"
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

def save_preferences(prefs):
    with open(MEMORY_FILE, "w") as f:
        json.dump(prefs, f)

def load_preferences():
    if not os.path.exists(MEMORY_FILE):
        return None
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def planner_agent(diet, allergies, cuisine, calories):
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
    return json.loads(response.content[0].text)

def recipe_agent(meal_name):
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
    return json.loads(response.content[0].text)

def shopper_agent(all_recipes):
    all_ingredients = []
    for day, meals in all_recipes.items():
        for meal_type, details in meals.items():
            all_ingredients.extend(details['recipe']['ingredients'])

    prompt = f"""
    Here is a list of ingredients from a 7-day meal plan:
    {json.dumps(all_ingredients)}

    Consolidate into a clean grocery shopping list. Combine duplicates and organize by category.
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
    return json.loads(response.content[0].text)

@app.route("/")
def index():
    saved = load_preferences()
    return render_template("index.html", saved=saved)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    diet = data.get("diet", "")
    allergies = data.get("allergies", "")
    cuisine = data.get("cuisine", "")
    calories = data.get("calories", "")

    save_preferences({"diet": diet, "allergies": allergies, "cuisine": cuisine, "calories": calories})

    try:
        meal_plan = planner_agent(diet, allergies, cuisine, calories)

        all_recipes = {}
        for day, meals in meal_plan.items():
            all_recipes[day] = {}
            for meal_type, meal_name in meals.items():
                recipe = recipe_agent(meal_name)
                all_recipes[day][meal_type] = {"name": meal_name, "recipe": recipe}

        shopping_list = shopper_agent(all_recipes)

        return jsonify({
            "success": True,
            "meal_plan": meal_plan,
            "recipes": all_recipes,
            "shopping_list": shopping_list
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
