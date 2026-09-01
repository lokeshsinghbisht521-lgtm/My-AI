import streamlit as st
import sqlite3
import json
import math
import requests
from io import BytesIO
from fractions import Fraction
from PIL import Image
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIG & MODERN CSS STYLING
# ==========================================
st.set_page_config(
    page_title="ChefAI - Smart Recipe Generator",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .hero-box {
        background: linear-gradient(135deg, #FF5F6D 0%, #FFC371 100%);
        border-radius: 24px;
        padding: 45px 30px;
        color: white;
        text-align: center;
        box-shadow: 0 15px 35px rgba(255, 95, 109, 0.25);
        margin-bottom: 30px;
    }
    
    .recipe-card {
        background: white;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
        border: 1px solid #f0f0f0;
        margin-bottom: 25px;
        transition: transform 0.2s ease;
    }
    
    .metric-pill {
        background: #F8F9FA;
        border: 1px solid #E9ECEF;
        border-radius: 12px;
        padding: 8px 14px;
        font-size: 13px;
        font-weight: 600;
        display: inline-block;
        margin: 4px;
    }
    
    .tag-pill {
        background: #EEF2FF;
        color: #4F46E5;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
    }
    
    .cooking-box {
        background: #0F172A;
        border-radius: 24px;
        padding: 40px;
        color: white;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. EMBEDDED DATA (RECIPES & SUBSTITUTIONS)
# ==========================================
SUBSTITUTIONS = {
    "chicken breast": ["tofu", "paneer", "turkey breast", "seitan", "chickpeas"],
    "chicken": ["tofu", "paneer", "turkey", "chickpeas", "mushrooms"],
    "beef": ["portobello mushrooms", "lentils", "ground turkey", "tofu"],
    "pork": ["chicken thigh", "turkey", "firm tofu"],
    "salmon": ["trout", "cod", "tofu", "halibut"],
    "shrimp": ["firm tofu", "scallops", "white fish", "mushrooms"],
    "butter": ["olive oil", "ghee", "coconut oil", "avocado oil"],
    "milk": ["oat milk", "almond milk", "soy milk", "coconut milk"],
    "heavy cream": ["coconut cream", "greek yogurt blended with milk", "cashew cream"],
    "eggs": ["flax egg (1 tbsp flax + 3 tbsp water)", "applesauce", "silken tofu"],
    "rice": ["quinoa", "cauliflower rice", "couscous", "bulgur"],
    "pasta": ["zucchini noodles (zoodles)", "spaghetti squash", "rice noodles"],
    "soy sauce": ["tamari (gluten-free)", "coconut aminos", "worcestershire sauce"],
    "broccoli": ["cauliflower", "green beans", "asparagus", "brussels sprouts"],
    "cheese": ["nutritional yeast", "vegan cheese", "avocado slices"],
    "garlic": ["shallots", "garlic powder (1/4 tsp per clove)", "onion powder"],
    "onion": ["shallots", "leeks", "green onions", "onion powder"],
    "tomatoes": ["canned diced tomatoes", "tomato paste + water", "red bell pepper"]
}

RECIPES_DATA = [
    {
        "id": 1,
        "name": "🍗 Honey Garlic Chicken & Rice Bowl",
        "description": "Tender glazed chicken bites served over fluffy steamed rice and crisp broccoli florets.",
        "image": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800",
        "cuisine": "Asian",
        "difficulty": "Easy",
        "prep_time": 10,
        "cook_time": 20,
        "total_time": 30,
        "servings": 4,
        "rating": 4.9,
        "dietary_tags": ["High Protein", "Gluten-Free"],
        "category": ["Dinner", "Quick Meals", "Under 30 Minutes"],
        "ingredients": [
            {"name": "chicken breast", "quantity": 500, "unit": "g"},
            {"name": "rice", "quantity": 2, "unit": "cups"},
            {"name": "broccoli", "quantity": 250, "unit": "g"},
            {"name": "garlic", "quantity": 4, "unit": "cloves"},
            {"name": "soy sauce", "quantity": 3, "unit": "tbsp"},
            {"name": "honey", "quantity": 3, "unit": "tbsp"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"}
        ],
        "steps": [
            {"number": 1, "instruction": "Rinse rice and cook in a rice cooker or pot with 4 cups of water.", "time": 20},
            {"number": 2, "instruction": "Cut chicken breast into bite-sized cubes. Season lightly with salt and pepper.", "time": 5},
            {"number": 3, "instruction": "Heat olive oil in a skillet over medium-high heat. Add chicken cubes and sear until golden (6-7 mins).", "time": 7},
            {"number": 4, "instruction": "Add minced garlic, soy sauce, and honey to the pan. Simmer for 3 minutes until a glossy glaze forms.", "time": 3},
            {"number": 5, "instruction": "Steam or pan-sear broccoli florets for 4-5 minutes until bright green and tender-crisp.", "time": 5},
            {"number": 6, "instruction": "Assemble bowls: Layer rice, top with glazed chicken, broccoli, and pour remaining pan sauce over top.", "time": 2}
        ],
        "nutrition": {"calories": 540, "protein": 44, "carbs": 66, "fat": 11, "fiber": 4}
    },
    {
        "id": 2,
        "name": "🍕 Neapolitan Margherita Pizza",
        "description": "Authentic crispy, bubbly crust topped with San Marzano tomatoes, fresh mozzarella, and sweet basil.",
        "image": "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=800",
        "cuisine": "Italian",
        "difficulty": "Medium",
        "prep_time": 25,
        "cook_time": 12,
        "total_time": 37,
        "servings": 2,
        "rating": 4.8,
        "dietary_tags": ["Vegetarian"],
        "category": ["Dinner", "Italian"],
        "ingredients": [
            {"name": "flour", "quantity": 300, "unit": "g"},
            {"name": "cheese", "quantity": 200, "unit": "g"},
            {"name": "tomatoes", "quantity": 3, "unit": "pieces"},
            {"name": "olive oil", "quantity": 2, "unit": "tbsp"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"}
        ],
        "steps": [
            {"number": 1, "instruction": "Preheat your oven to its highest temperature (preferably 500°F / 260°C).", "time": 15},
            {"number": 2, "instruction": "Stretch pizza dough on a floured surface into a 12-inch round base.", "time": 5},
            {"number": 3, "instruction": "Crush fresh tomatoes with minced garlic, olive oil, and a pinch of salt. Spread over dough.", "time": 3},
            {"number": 4, "instruction": "Tear fresh mozzarella cheese into chunks and scatter across the pizza.", "time": 2},
            {"number": 5, "instruction": "Bake for 10-12 minutes until crust is charred and cheese is melted and bubbling.", "time": 12},
            {"number": 6, "instruction": "Garnish with fresh basil leaves and a drizzle of olive oil before slicing.", "time": 1}
        ],
        "nutrition": {"calories": 610, "protein": 24, "carbs": 76, "fat": 22, "fiber": 4}
    },
    {
        "id": 3,
        "name": "🥑 High-Protein Loaded Avocado Toast",
        "description": "Artisan toasted sourdough topped with chunky lemon avocado, soft poached eggs, and chili flakes.",
        "image": "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=800",
        "cuisine": "American",
        "difficulty": "Easy",
        "prep_time": 5,
        "cook_time": 8,
        "total_time": 13,
        "servings": 2,
        "rating": 4.7,
        "dietary_tags": ["Vegetarian", "High Protein", "Healthy"],
        "category": ["Breakfast", "Quick Meals", "Under 30 Minutes"],
        "ingredients": [
            {"name": "bread", "quantity": 2, "unit": "slices"},
            {"name": "eggs", "quantity": 4, "unit": "pieces"},
            {"name": "avocado", "quantity": 1, "unit": "pieces"},
            {"name": "olive oil", "quantity": 1, "unit": "tbsp"},
            {"name": "tomatoes", "quantity": 1, "unit": "pieces"}
        ],
        "steps": [
            {"number": 1, "instruction": "Toast sourdough bread slices until golden brown and sturdy.", "time": 3},
            {"number": 2, "instruction": "Mash avocado in a bowl with lemon juice, salt, pepper, and diced tomatoes.", "time": 3},
            {"number": 3, "instruction": "Poach or fry eggs in a non-stick skillet to your desired yolk runniness.", "time": 4},
            {"number": 4, "instruction": "Spread mashed avocado evenly on toast and top with warm eggs and red pepper flakes.", "time": 2}
        ],
        "nutrition": {"calories": 390, "protein": 19, "carbs": 32, "fat": 21, "fiber": 7}
    },
    {
        "id": 4,
        "name": "🌮 Sizzling Mexican Beef Tacos",
        "description": "Zesty spiced ground beef in warm corn tortillas, garnished with cilantro, onions, and lime.",
        "image": "https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?w=800",
        "cuisine": "Mexican",
        "difficulty": "Easy",
        "prep_time": 10,
        "cook_time": 15,
        "total_time": 25,
        "servings": 4,
        "rating": 4.9,
        "dietary_tags": ["High Protein", "Gluten-Free"],
        "category": ["Dinner", "Quick Meals", "Under 30 Minutes"],
        "ingredients": [
            {"name": "beef", "quantity": 500, "unit": "g"},
            {"name": "onion", "quantity": 1, "unit": "pieces"},
            {"name": "garlic", "quantity": 3, "unit": "cloves"},
            {"name": "tomatoes", "quantity": 2, "unit": "pieces"},
            {"name": "cheese", "quantity": 100, "unit": "g"}
        ],
        "steps": [
            {"number": 1, "instruction": "Dice onion, garlic, and tomatoes.", "time": 5},
            {"number": 2, "instruction": "Brown ground beef in a skillet over medium heat, draining excess fat.", "time": 7},
            {"number": 3, "instruction": "Add onions, garlic, cumin, chili powder, and tomatoes. Simmer for 5 minutes.", "time": 5},
            {"number": 4, "instruction": "Warm taco shells in the oven or dry skillet. Spoon in meat and top with cheese.", "time": 3}
        ],
        "nutrition": {"calories": 480, "protein": 36, "carbs": 28, "fat": 24, "fiber": 4}
    },
    {
        "id": 5,
        "name": "🍛 Creamy Butter Chicken / Paneer",
        "description": "Rich, silky tomato and cashew-spiced curry infused with aromatic garam masala.",
        "image": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=800",
        "cuisine": "Indian",
        "difficulty": "Medium",
        "prep_time": 15,
        "cook_time": 25,
        "total_time": 40,
        "servings": 4,
        "rating": 4.9,
        "dietary_tags": ["High Protein", "Gluten-Free"],
        "category": ["Dinner", "Indian"],
        "ingredients": [
            {"name": "chicken breast", "quantity": 600, "unit": "g"},
            {"name": "butter", "quantity": 3, "unit": "tbsp"},
            {"name": "heavy cream", "quantity": 0.5, "unit": "cups"},
            {"name": "tomatoes", "quantity": 4, "unit": "pieces"},
            {"name": "onion", "quantity": 1, "unit": "pieces"},
            {"name": "garlic", "quantity": 4, "unit": "cloves"}
        ],
        "steps": [
            {"number": 1, "instruction": "Sear chicken cubes in 1 tbsp butter until cooked through. Set aside.", "time": 8},
            {"number": 2, "instruction": "Sauté chopped onions, garlic, and diced tomatoes until soft.", "time": 7},
            {"number": 3, "instruction": "Blend tomato mixture into a silky puree and return to the skillet.", "time": 3},
            {"number": 4, "instruction": "Stir in remaining butter, heavy cream, and garam masala. Add chicken and simmer for 5 mins.", "time": 6}
        ],
        "nutrition": {"calories": 520, "protein": 41, "carbs": 16, "fat": 32, "fiber": 3}
    },
    {
        "id": 6,
        "name": "🍝 Roman Spaghetti Carbonara",
        "description": "Classic creamy pasta created strictly from eggs, sharp cheese, black pepper, and crispy meat.",
        "image": "https://images.unsplash.com/photo-1612874742237-6526221588e3?w=800",
        "cuisine": "Italian",
        "difficulty": "Medium",
        "prep_time": 10,
        "cook_time": 15,
        "total_time": 25,
        "servings": 3,
        "rating": 4.8,
        "dietary_tags": ["High Protein"],
        "category": ["Dinner", "Italian", "Under 30 Minutes"],
        "ingredients": [
            {"name": "pasta", "quantity": 350, "unit": "g"},
            {"name": "eggs", "quantity": 3, "unit": "pieces"},
            {"name": "cheese", "quantity": 100, "unit": "g"},
            {"name": "garlic", "quantity": 2, "unit": "cloves"}
        ],
        "steps": [
            {"number": 1, "instruction": "Boil pasta in generously salted water until al dente. Reserve 1 cup pasta water.", "time": 10},
            {"number": 2, "instruction": "In a bowl, whisk eggs with finely grated cheese and plenty of cracked black pepper.", "time": 3},
            {"number": 3, "instruction": "Drain pasta and toss while hot into the egg-cheese mixture off heat to create a glossy sauce.", "time": 3}
        ],
        "nutrition": {"calories": 560, "protein": 26, "carbs": 70, "fat": 18, "fiber": 3}
    }
]

# ==========================================
# 3. DATABASE & SESSION STATE
# ==========================================
def init_db():
    conn = sqlite3.connect("recipes_app.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY, recipe_id INTEGER UNIQUE, name TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS recent_searches (id INTEGER PRIMARY KEY, query TEXT)""")
    conn.commit()
    conn.close()

init_db()

def get_favorites():
    conn = sqlite3.connect("recipes_app.db")
    c = conn.cursor()
    c.execute("SELECT recipe_id FROM favorites")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]

def toggle_favorite(recipe_id, recipe_name):
    conn = sqlite3.connect("recipes_app.db")
    c = conn.cursor()
    c.execute("SELECT id FROM favorites WHERE recipe_id = ?", (recipe_id,))
    if c.fetchone():
        c.execute("DELETE FROM favorites WHERE recipe_id = ?", (recipe_id,))
    else:
        c.execute("INSERT OR IGNORE INTO favorites (recipe_id, name) VALUES (?, ?)", (recipe_id, recipe_name))
    conn.commit()
    conn.close()

if 'view' not in st.session_state: st.session_state.view = 'home'
if 'selected_recipe' not in st.session_state: st.session_state.selected_recipe = None
if 'cooking_step' not in st.session_state: st.session_state.cooking_step = 0
if 'search_query' not in st.session_state: st.session_state.search_query = ""
if 'servings_scale' not in st.session_state: st.session_state.servings_scale = {}

# ==========================================
# 4. HELPER ENGINES
# ==========================================
def format_qty(qty):
    frac = Fraction(qty).limit_denominator(8)
    if frac.denominator == 1:
        return str(frac.numerator)
    whole = frac.numerator // frac.denominator
    rem = frac.numerator % frac.denominator
    return f"{whole} {rem}/{frac.denominator}" if whole > 0 else f"{rem}/{frac.denominator}"

def search_engine(user_input):
    if not user_input.strip():
        return [(r, 100, []) for r in RECIPES_DATA]
    
    tokens = [t.strip().lower() for t in user_input.replace(",", " ").split() if t.strip()]
    results = []
    
    for r in RECIPES_DATA:
        rec_ings = [i["name"].lower() for i in r["ingredients"]]
        matched_ings = []
        
        for token in tokens:
            for ing in rec_ings:
                if token in ing or ing in token:
                    matched_ings.append(ing)
                    break
        
        matched_ings = list(set(matched_ings))
        total_ings = len(rec_ings)
        match_pct = round((len(matched_ings) / total_ings) * 100) if total_ings else 0
        missing_ings = [i["name"] for i in r["ingredients"] if i["name"].lower() not in matched_ings]
        
        # Name/Category match boosts score
        for token in tokens:
            if token in r["name"].lower() or any(token in c.lower() for c in r.get("category", [])):
                match_pct = max(match_pct, 90)
                
        results.append((r, match_pct, missing_ings))
        
    results.sort(key=lambda x: x[1], reverse=True)
    return results

# ==========================================
# 5. UI COMPONENTS
# ==========================================
def render_recipe_card(recipe, match_score=None, missing=[]):
    favs = get_favorites()
    is_fav = recipe["id"] in favs
    
    with st.container():
        st.markdown('<div class="recipe-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(recipe["image"], use_container_width=True)
            
        with col2:
            st.markdown(f"### {recipe['name']}")
            
            # Tags & Pills
            tags_html = "".join([f'<span class="tag-pill">{t}</span>' for t in recipe["dietary_tags"]])
            st.markdown(f"{tags_html}", unsafe_allow_html=True)
            
            # Key Details
            st.markdown(f"""
            <div style="margin: 10px 0;">
                <span class="metric-pill">⏱️ {recipe['total_time']} min</span>
                <span class="metric-pill">⚡ {recipe['difficulty']}</span>
                <span class="metric-pill">🍽️ {recipe['servings']} servings</span>
                <span class="metric-pill">⭐ {recipe['rating']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if match_score is not None and match_score > 0:
                color = "#10B981" if match_score >= 70 else "#F59E0B"
                st.markdown(f"**Match:** <span style='color:{color}; font-weight:700;'>{match_score}% ingredients matched</span>", unsafe_allow_html=True)
                if missing:
                    st.caption(f"Missing: {', '.join(missing[:3])}")
            
            st.write(recipe["description"])
            
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("👨‍🍳 Cook This Recipe", key=f"view_{recipe['id']}", use_container_width=True):
                    st.session_state.selected_recipe = recipe
                    st.session_state.cooking_step = 0
                    st.session_state.view = 'detail'
                    st.rerun()
            with c_btn2:
                btn_label = "❤️ Saved" if is_fav else "🤍 Save"
                if st.button(btn_label, key=f"fav_{recipe['id']}", use_container_width=True):
                    toggle_favorite(recipe["id"], recipe["name"])
                    st.rerun()
                    
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. APP VIEWS
# ==========================================
def view_home():
    st.markdown("""
    <div class="hero-box">
        <h1 style="font-size: 40px; font-weight:800; margin-bottom: 10px;">🍳 What's in your kitchen?</h1>
        <p style="font-size: 18px; opacity: 0.95;">Turn your everyday ingredients into delicious home-cooked meals.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search Box
    col_s1, col_s2 = st.columns([4, 1])
    with col_s1:
        query = st.text_input(
            "Search by ingredients or dish name",
            placeholder="e.g. chicken, rice, broccoli OR pasta, pizza, tacos...",
            value=st.session_state.search_query,
            label_visibility="collapsed"
        )
    with col_s2:
        search_clicked = st.button("🔍 Find Recipes", type="primary", use_container_width=True)
        
    # Quick Categories
    st.markdown("#### Quick Categories")
    cat_cols = st.columns(6)
    categories = ["⚡ Under 30 Minutes", "🌱 Vegetarian", "🥩 High Protein", "🍝 Italian", "🌶️ Indian", "🥑 Healthy"]
    for i, cat in enumerate(categories):
        with cat_cols[i]:
            if st.button(cat, key=f"cat_{i}", use_container_width=True):
                st.session_state.search_query = cat.split()[-1]
                st.rerun()
                
    st.markdown("---")
    
    # Results
    results = search_engine(query)
    st.subheader(f"💡 Recommended Recipes ({len(results)})")
    
    for r, score, missing in results:
        render_recipe_card(r, score, missing)

def view_detail():
    recipe = st.session_state.selected_recipe
    if not recipe:
        st.session_state.view = 'home'
        st.rerun()
        
    if st.button("⬅️ Back to Search"):
        st.session_state.view = 'home'
        st.rerun()
        
    st.markdown(f"# {recipe['name']}")
    
    # Servings Scaler
    orig_servings = recipe["servings"]
    current_servings = st.session_state.servings_scale.get(recipe["id"], orig_servings)
    
    col_top1, col_top2 = st.columns([2, 1])
    with col_top1:
        st.image(recipe["image"], use_container_width=True)
    with col_top2:
        st.markdown("### ⚙️ Adjust Servings")
        col_m, col_p = st.columns(2)
        with col_m:
            if st.button("➖ Decrease", use_container_width=True) and current_servings > 1:
                st.session_state.servings_scale[recipe["id"]] = current_servings - 1
                st.rerun()
        with col_p:
            if st.button("➕ Increase", use_container_width=True) and current_servings < 16:
                st.session_state.servings_scale[recipe["id"]] = current_servings + 1
                st.rerun()
                
        st.markdown(f"<h3 style='text-align:center;'>Serving: <b>{current_servings}</b> portions</h3>", unsafe_allow_html=True)
        
        # Macros
        scale = current_servings / orig_servings
        n = recipe["nutrition"]
        st.markdown(f"""
        <div style="background:#F8FAFC; border-radius:16px; padding:16px; margin-top:10px;">
            <b>🔥 Estimated Nutrition (Per Serving):</b><br>
            • Calories: <b>{round(n['calories'])} kcal</b><br>
            • Protein: <b>{round(n['protein'])}g</b><br>
            • Carbs: <b>{round(n['carbs'])}g</b><br>
            • Fats: <b>{round(n['fat'])}g</b>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("👨‍🍳 Enter Distraction-Free Cooking Mode", type="primary", use_container_width=True):
            st.session_state.view = 'cooking'
            st.session_state.cooking_step = 0
            st.rerun()

    st.markdown("---")
    
    # Ingredients & Substitutions
    col_ing, col_steps = st.columns([1, 1])
    
    with col_ing:
        st.markdown("### 🛒 Scaled Ingredients")
        scale = current_servings / orig_servings
        for ing in recipe["ingredients"]:
            qty_scaled = format_qty(ing["quantity"] * scale)
            subs = SUBSTITUTIONS.get(ing["name"].lower(), [])
            sub_text = f" *(Swap: {', '.join(subs[:2])})*" if subs else ""
            st.markdown(f"• **{qty_scaled} {ing['unit']}** {ing['name']}{sub_text}")
            
    with col_steps:
        st.markdown("### 📋 Step-by-Step Instructions")
        for step in recipe["steps"]:
            st.markdown(f"**Step {step['number']}:** {step['instruction']} *(~{step.get('time', 5)} mins)*")

def view_cooking():
    recipe = st.session_state.selected_recipe
    steps = recipe["steps"]
    step_idx = st.session_state.cooking_step
    curr_step = steps[step_idx]
    
    st.progress((step_idx + 1) / len(steps))
    
    st.markdown(f"""
    <div class="cooking-box">
        <h4 style="color:#94A3B8; text-transform:uppercase; letter-spacing:2px;">Step {step_idx + 1} of {len(steps)}</h4>
        <h1 style="font-size:38px; line-height:1.4; margin:30px 0; font-weight:700;">{curr_step['instruction']}</h1>
        <span style="background:rgba(255,255,255,0.15); padding:10px 20px; border-radius:30px; font-size:18px;">⏱️ Timer: {curr_step.get('time', 5)} Minutes</span>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("⬅️ Previous", use_container_width=True, disabled=(step_idx == 0)):
            st.session_state.cooking_step -= 1
            st.rerun()
    with c2:
        if st.button("❌ Exit Cooking Mode", use_container_width=True):
            st.session_state.view = 'detail'
            st.rerun()
    with c3:
        if step_idx < len(steps) - 1:
            if st.button("Next ➡️", type="primary", use_container_width=True):
                st.session_state.cooking_step += 1
                st.rerun()
        else:
            if st.button("🎉 Finish Meal!", type="primary", use_container_width=True):
                st.balloons()
                st.success("Bon Appétit! Hope you enjoy your meal!")
                st.session_state.view = 'home'
                st.rerun()

# ==========================================
# 7. ROUTING
# ==========================================
if st.session_state.view == 'home':
    view_home()
elif st.session_state.view == 'detail':
    view_detail()
elif st.session_state.view == 'cooking':
    view_cooking()