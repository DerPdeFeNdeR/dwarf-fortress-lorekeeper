"""Verified method details; raw/unknown tokens never become guessed mechanics."""
DEATH_CAUSES = {
    'OLD_AGE': 'old age', 'HUNGER': 'starvation', 'THIRST': 'dehydration',
    'SHOT': 'being shot', 'BLEED': 'blood loss', 'DROWN': 'drowning',
    'SUFFOCATE': 'suffocation', 'COLLISION': 'a collision',
    'MAGMA': 'magma', 'MAGMA_MIST': 'magma mist', 'DRAGONFIRE': 'dragon fire',
    'FIRE': 'fire', 'CAVEIN': 'a cave-in', 'DRAWBRIDGE': 'a drawbridge',
    'FALLING_ROCKS': 'falling rocks', 'TRAP': 'a trap',
    'HEAT': 'heat', 'COLD': 'cold', 'BEHEAD': 'beheading', 'INFECTION': 'infection',
}
INJURIES = {'BLUDGEON': 'blunt trauma', 'SLASH': 'slashing',
            'PIERCE': 'piercing', 'GORE': 'goring', 'BURN': 'burning'}


def details(event):
    method = event.get('method') or {}
    if method and (method.get('status') != 'available' or method.get('source_event_id') != event['id']):
        method = {}
    rows = []
    if event['kind'] == 'death':
        cause = DEATH_CAUSES.get(method.get('death_cause', event.get('death_cause')))
        if cause:
            rows.append('the cause of death was ' + cause)
        for item in method.get('weapons', [])[:2]:
            if item.get('status') == 'resolved' and item.get('name'):
                if item.get('role') == 'impact_item':
                    rows.append('the weapon was ' + item['name'])
                elif item.get('role') == 'launcher':
                    rows.append('the launcher was ' + item['name'])
    elif event['kind'] == 'wounding':
        injury = INJURIES.get(method.get('injury_type'))
        if injury:
            rows.append('the injury involved ' + injury)
        if method.get('body_part'):
            rows.append('the injured body part was ' + method['body_part'])
        if method.get('part_lost') is True:
            rows.append('the body part was lost')
    return rows
