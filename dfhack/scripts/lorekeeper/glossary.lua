-- Deterministic labels for common Lorekeeper tokens.
--
-- Unknown tokens intentionally remain marked as unknown. This glossary adds
-- readable labels; it does not infer explanations from unfamiliar values.
--@module = true

local thought_labels = {
    SawDeadBody='Saw a dead body',
    Talked='Had a conversation',
    AdmireArrangedBuilding='Admired an arranged building',
    WatchPerform='Watched a performance',
    Syndrome='Experienced a syndrome-related effect',
}

local emotion_labels = {
    ANYTHING='No specific emotion',
    FONDNESS='Fondness',
    INTEREST='Interest',
    DELIGHT='Delight',
    EUPHORIA='Euphoria',
}

local facet_labels = {
    ABSTRACT_INCLINED='Abstract thinking',
    ACTIVITY_LEVEL='Activity level',
    ALTRUISM='Altruism',
    ANGER_PROPENSITY='Anger propensity',
    ANXIETY_PROPENSITY='Anxiety propensity',
    ART_INCLINED='Artistic inclination',
    CHEER_PROPENSITY='Cheerfulness',
    CONFIDENCE='Confidence',
    CURIOUS='Curiosity',
    DEPRESSION_PROPENSITY='Depression propensity',
    FRIENDLINESS='Friendliness',
    GREGARIOUSNESS='Sociability',
    STRESS_VULNERABILITY='Stress vulnerability',
    SWAYED_BY_EMOTIONS='Influence of emotions',
    TRUST='Trust',
}

local function unknown(kind, token)
    return {
        known=false,
        text=('Unknown %s token: %s'):format(kind, token),
        raw=token,
    }
end

local function describe(labels, kind, token)
    local text = labels[token]
    if not text then
        return unknown(kind, token)
    end

    return {
        known=true,
        text=text,
        raw=token,
    }
end

function describe_thought(token)
    return describe(thought_labels, 'thought', token)
end

function describe_emotion(token)
    return describe(emotion_labels, 'emotion', token)
end

function describe_facet(token)
    return describe(facet_labels, 'personality', token)
end
