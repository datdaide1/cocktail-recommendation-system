class MenuExporter:
    """
    Utility class to handle exporting customized cocktail menus to standard HTML.
    Supports premium CSS/HTML styling suitable for printing or downloading.
    """
    def __init__(self, menu_title="THE ARTISAN LOUNGE"):
        self.menu_title = menu_title.upper()
        
    def generate_html_menu(self, cocktails_list: list) -> str:
        """
        Generates a premium CSS/HTML layout of the selected cocktails.
        
        Args:
            cocktails_list: List of dicts representing cocktail records from the database.
            
        Returns:
            HTML string representation of the menu.
        """
        items_html = ""
        for item in cocktails_list:
            name = item.get("name", "Unnamed Cocktail")
            category = item.get("category", "Classic")
            glass = item.get("glassware_recommendation", item.get("glassType", "Cocktail Glass"))
            abv = item.get("abv_category", "Medium ABV")
            ingredients = item.get("ingredients", "")
            instructions = item.get("instructions", "")
            meaning = item.get("meaning_and_history", "")
            
            # Format ingredients list if it's stored as string representation of a list
            try:
                ing_list = eval(ingredients)
                ingredients_formatted = ", ".join(ing_list)
            except:
                ingredients_formatted = str(ingredients)
                
            items_html += f"""
            <div class="menu-item">
                <div class="menu-header">
                    <span class="drink-name">{name}</span>
                    <span class="drink-meta">{category} | {glass}</span>
                </div>
                <div class="drink-ingredients">{ingredients_formatted}</div>
                <div class="drink-instructions">{instructions}</div>
                {f'<div class="drink-meaning"><em>History: {meaning}</em></div>' if meaning else ''}
                <div class="drink-abv">Strength: {abv}</div>
            </div>
            """
            
        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>{self.menu_title}</title>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700&family=Montserrat:ital,wght@0,300;0,400;1,300&display=swap');
                
                body {{
                    font-family: 'Montserrat', sans-serif;
                    background-color: #0c0f17;
                    color: #f1f3f8;
                    margin: 0;
                    padding: 40px;
                    display: flex;
                    justify-content: center;
                }}
                .menu-container {{
                    width: 100%;
                    max-width: 800px;
                    border: 2px solid #c5a059;
                    padding: 40px;
                    background-color: #121622;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                    border-radius: 4px;
                }}
                .menu-title {{
                    font-family: 'Cinzel', serif;
                    text-align: center;
                    font-size: 2.5em;
                    color: #c5a059;
                    letter-spacing: 4px;
                    margin-bottom: 5px;
                    font-weight: 700;
                }}
                .menu-subtitle {{
                    font-family: 'Cinzel', serif;
                    text-align: center;
                    font-size: 0.9em;
                    color: #8b9bb4;
                    letter-spacing: 2px;
                    text-transform: uppercase;
                    margin-bottom: 40px;
                }}
                .divider {{
                    height: 1px;
                    background-color: #c5a059;
                    width: 60%;
                    margin: 0 auto 40px auto;
                }}
                .menu-item {{
                    margin-bottom: 35px;
                    page-break-inside: avoid;
                    border-bottom: 1px solid #1c2335;
                    padding-bottom: 20px;
                }}
                .menu-item:last-child {{
                    border-bottom: none;
                }}
                .menu-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    margin-bottom: 8px;
                }}
                .drink-name {{
                    font-family: 'Cinzel', serif;
                    font-size: 1.35em;
                    color: #c5a059;
                    font-weight: 700;
                }}
                .drink-meta {{
                    font-size: 0.8em;
                    color: #8b9bb4;
                    font-style: italic;
                }}
                .drink-ingredients {{
                    font-size: 0.95em;
                    color: #d1d9e6;
                    font-style: italic;
                    margin-bottom: 6px;
                }}
                .drink-instructions {{
                    font-size: 0.9em;
                    color: #a3afc2;
                    margin-bottom: 8px;
                    line-height: 1.4;
                }}
                .drink-meaning {{
                    font-size: 0.85em;
                    color: #8b9bb4;
                    margin-bottom: 6px;
                }}
                .drink-abv {{
                    font-size: 0.8em;
                    color: #c5a059;
                    text-transform: uppercase;
                    font-weight: bold;
                    letter-spacing: 1px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 0.8em;
                    color: #56657a;
                    margin-top: 50px;
                    letter-spacing: 1px;
                    text-transform: uppercase;
                }}
            </style>
        </head>
        <body>
            <div class="menu-container">
                <div class="menu-title">{self.menu_title}</div>
                <div class="menu-subtitle">Fine Selection of Curated Drinks</div>
                <div class="divider"></div>
                <div class="menu-content">
                    {items_html}
                </div>
                <div class="footer">Crafted with AI Lounge Assistant</div>
            </div>
        </body>
        </html>
        """
        return html_template
