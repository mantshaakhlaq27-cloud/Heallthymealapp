# Import required libraries
from flask import Flask, render_template, request
import requests
import json
import os
import random

# Initialize Flask app
app = Flask(__name__)

# Configuration for Spoonacular API
# Get your free API key from: https://spoonacular.com/food-api
SPOONACULAR_API_KEY = os.environ.get('SPOONACULAR_API_KEY', 'dc1cd0f108e64554be4de5bed590e37f')
SPOONACULAR_BASE_URL = 'https://api.spoonacular.com/recipes'

# Home route - displays the main page with auto recommendations
@app.route('/')
def index():
    # Get random recipe recommendations for the home page
    recommended_recipes = get_recommended_recipes()
    return render_template('index.html', recommended_recipes=recommended_recipes)

# Search route - handles ingredient submission and fetches recipes
@app.route('/search', methods=['POST'])
def search():
    # Get ingredients from the form
    ingredients = request.form.get('ingredients', '')
    
    # Try to fetch from Spoonacular API first
    recipes = fetch_from_spoonacular(ingredients)
    
    # If API fails or no key provided, use local dataset
    if not recipes:
        recipes = fetch_from_local_dataset(ingredients)
    
    return render_template('result.html', recipes=recipes, ingredients=ingredients)

# Function to get recommended recipes for home page
def get_recommended_recipes():
    """
    Gets random healthy recipe recommendations to display on home page
    Returns a list of 3 recommended recipes
    """
    try:
        # Load local recipes database
        with open('local_recipes.json', 'r') as file:
            all_recipes = json.load(file)
        
        # Select 3 random recipes
        if len(all_recipes) >= 3:
            recommended = random.sample(all_recipes, 3)
        else:
            recommended = all_recipes
        
        return recommended
    
    except FileNotFoundError:
        # Return default recommendations if file not found
        return get_default_recommendations()
    except Exception as e:
        print(f"Error loading recommendations: {e}")
        return get_default_recommendations()

# Function to provide default recommendations
def get_default_recommendations():
    """
    Returns default recipe recommendations
    """
    return [
        {
            'name': 'Banana Oat Pancakes',
            'image': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=300&fit=crop',
            'description': 'Fluffy, healthy pancakes made with bananas and oats.',
            'calories': 320,
            'protein': 12,
            'fat': 8,
            'health_benefits': ['High in fiber', 'Energy boosting', 'Heart healthy'],
            'youtube_url': 'https://www.youtube.com/results?search_query=banana+oat+pancakes+recipe',
            'ingredients': ['banana', 'oats', 'eggs', 'milk']
        },
        {
            'name': 'Grilled Chicken & Rice Bowl',
            'image': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop',
            'description': 'A protein-packed bowl with tender grilled chicken and fluffy rice.',
            'calories': 450,
            'protein': 35,
            'fat': 12,
            'health_benefits': ['High protein', 'Muscle building', 'Balanced macros'],
            'youtube_url': 'https://www.youtube.com/results?search_query=grilled+chicken+rice+bowl+recipe',
            'ingredients': ['chicken', 'rice', 'broccoli', 'carrots']
        },
        {
            'name': 'Quinoa Salad Bowl',
            'image': 'https://images.unsplash.com/photo-1505253716362-afaea1d3d1af?w=400&h=300&fit=crop',
            'description': 'Refreshing quinoa salad with fresh vegetables and lemon dressing.',
            'calories': 350,
            'protein': 14,
            'fat': 15,
            'health_benefits': ['Complete protein', 'Gluten-free', 'Rich in fiber'],
            'youtube_url': 'https://www.youtube.com/results?search_query=quinoa+salad+bowl+recipe',
            'ingredients': ['quinoa', 'tomatoes', 'cucumber', 'lemon']
        }
    ]

# Function to fetch recipes from Spoonacular API
def fetch_from_spoonacular(ingredients):
    """
    Fetches recipes from Spoonacular API based on ingredients
    Returns a list of formatted recipe dictionaries
    """
    # Check if API key is set
    if SPOONACULAR_API_KEY == 'YOUR_API_KEY_HERE':
        return None
    
    try:
        # API endpoint for finding recipes by ingredients
        url = f'{SPOONACULAR_BASE_URL}/findByIngredients'
        params = {
            'apiKey': SPOONACULAR_API_KEY,
            'ingredients': ingredients,
            'number': 6,  # Number of recipes to return
            'ranking': 1,  # Minimize missing ingredients
            'ignorePantry': True
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            recipes_data = response.json()
            formatted_recipes = []
            
            # Format each recipe with detailed information
            for recipe in recipes_data:
                recipe_id = recipe['id']
                
                # Get detailed recipe information
                detail_url = f'{SPOONACULAR_BASE_URL}/{recipe_id}/information'
                detail_params = {'apiKey': SPOONACULAR_API_KEY}
                detail_response = requests.get(detail_url, params=detail_params, timeout=10)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    
                    # Extract nutritional information
                    nutrition = detail_data.get('nutrition', {})
                    nutrients = nutrition.get('nutrients', [])
                    
                    calories = next((n['amount'] for n in nutrients if n['name'] == 'Calories'), 'N/A')
                    protein = next((n['amount'] for n in nutrients if n['name'] == 'Protein'), 'N/A')
                    fat = next((n['amount'] for n in nutrients if n['name'] == 'Fat'), 'N/A')
                    
                    # Search for YouTube video
                    youtube_url = search_youtube_video(recipe['title'])
                    
                    formatted_recipe = {
                        'name': recipe['title'],
                        'image': recipe.get('image', 'https://via.placeholder.com/300x200?text=No+Image'),
                        'description': detail_data.get('summary', 'A delicious and healthy recipe!'),
                        'calories': calories,
                        'protein': protein,
                        'fat': fat,
                        'health_benefits': extract_health_benefits(detail_data),
                        'youtube_url': youtube_url,
                        'source_url': detail_data.get('sourceUrl', '#')
                    }
                    formatted_recipes.append(formatted_recipe)
            
            return formatted_recipes
        
    except Exception as e:
        print(f"Error fetching from Spoonacular: {e}")
        return None
    
    return None

# Function to search YouTube for recipe videos
def search_youtube_video(recipe_name):
    """
    Generates a YouTube search URL for the recipe
    Returns embedded YouTube URL
    """
    # Clean recipe name for search
    search_query = recipe_name.replace(' ', '+') + '+recipe+tutorial'
    
    # Return YouTube search results (you can integrate YouTube API for specific videos)
    # For now, we'll return a search URL that opens in YouTube
    return f"https://www.youtube.com/results?search_query={search_query}"

# Function to extract health benefits from recipe data
def extract_health_benefits(recipe_data):
    """
    Extracts health-related information from recipe data
    Returns a list of health benefits
    """
    benefits = []
    
    # Check if recipe is vegetarian, vegan, gluten-free, etc.
    if recipe_data.get('vegetarian'):
        benefits.append('Vegetarian-friendly')
    if recipe_data.get('vegan'):
        benefits.append('Vegan-friendly')
    if recipe_data.get('glutenFree'):
        benefits.append('Gluten-free')
    if recipe_data.get('dairyFree'):
        benefits.append('Dairy-free')
    if recipe_data.get('veryHealthy'):
        benefits.append('Very healthy option')
    
    # If no specific benefits, add general ones
    if not benefits:
        benefits = ['Nutritious meal', 'Balanced ingredients', 'Home-cooked goodness']
    
    return benefits

# Function to fetch recipes from local JSON dataset
def fetch_from_local_dataset(ingredients):
    """
    Fetches recipes from local JSON file when API is unavailable
    Returns a list of matching recipes
    """
    try:
        # Load local recipes database
        with open('local_recipes.json', 'r') as file:
            all_recipes = json.load(file)
        
        # Convert ingredients to lowercase for matching
        ingredient_list = [ing.strip().lower() for ing in ingredients.split(',')]
        
        # Find matching recipes
        matching_recipes = []
        for recipe in all_recipes:
            # Check if any of the user's ingredients match recipe ingredients
            recipe_ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
            
            # Calculate match score
            matches = sum(1 for ing in ingredient_list if any(ing in r_ing for r_ing in recipe_ingredients))
            
            if matches > 0:
                recipe['match_score'] = matches
                matching_recipes.append(recipe)
        
        # Sort by match score and return top 6
        matching_recipes.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        return matching_recipes[:6]
    
    except FileNotFoundError:
        # Return default recipes if file not found
        return get_default_recipes()
    except Exception as e:
        print(f"Error loading local recipes: {e}")
        return get_default_recipes()

# Function to provide default recipes as fallback
def get_default_recipes():
    """
    Returns default recipes when all other methods fail
    """
    return [
        {
            'name': 'Banana Oat Smoothie',
            'image': 'https://via.placeholder.com/300x200?text=Banana+Oat+Smoothie',
            'description': 'A creamy and nutritious smoothie perfect for breakfast or post-workout.',
            'calories': 250,
            'protein': 8,
            'fat': 5,
            'health_benefits': ['High in fiber', 'Energy boosting', 'Heart healthy'],
            'youtube_url': 'https://www.youtube.com/results?search_query=banana+oat+smoothie+recipe',
            'ingredients': ['banana', 'oats', 'milk', 'honey']
        }
    ]

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)