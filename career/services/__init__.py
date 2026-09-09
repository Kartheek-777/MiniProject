from placement_copilot.services.roadmap_engine import generate_career_roadmap, get_fallback_roadmap

def generate_career_roadmap_ai(target_role, current_skills, missing_skills):
    """
    Helper function returning roadmap JSON dictionary.
    """
    fallback = get_fallback_roadmap(target_role, current_skills, missing_skills, 'Intermediate')
    return fallback
