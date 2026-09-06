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
    SatisfiedAtWork='Felt satisfied at work',
}

local emotion_labels = {
    ANYTHING='No specific emotion',
    FONDNESS='Fondness',
    INTEREST='Interest',
    DELIGHT='Delight',
    EUPHORIA='Euphoria',
    SATISFACTION='Satisfaction',
}

local facet_labels = {
    ABSTRACT_INCLINED='Abstract thinking',
    ACTIVITY_LEVEL='Activity level',
    ALTRUISM='Altruism',
    AMBITION='Ambition',
    ANGER_PROPENSITY='Anger propensity',
    ANXIETY_PROPENSITY='Anxiety propensity',
    ART_INCLINED='Artistic inclination',
    ASSERTIVENESS='Assertiveness',
    BASHFUL='Bashfulness',
    BRAVERY='Bravery',
    CHEER_PROPENSITY='Cheerfulness',
    CLOSEMINDED='Closed-mindedness',
    CONFIDENCE='Confidence',
    CRUELTY='Cruelty',
    CURIOUS='Curiosity',
    DEPRESSION_PROPENSITY='Depression propensity',
    DISCORD='Disagreement propensity',
    DISDAIN_ADVICE='Disdain for advice',
    DUTIFULNESS='Dutifulness',
    EMOTIONALLY_OBSESSIVE='Emotional obsessiveness',
    ENVY_PROPENSITY='Envy propensity',
    EXCITEMENT_SEEKING='Excitement seeking',
    FRIENDLINESS='Friendliness',
    GRATITUDE='Gratitude',
    GREED='Greed',
    GREGARIOUSNESS='Sociability',
    HATE_PROPENSITY='Hate propensity',
    HOPEFUL='Hopefulness',
    HUMOR='Sense of humor',
    IMAGINATION='Imagination',
    IMMODERATION='Immoderation',
    IMMODESTY='Immodesty',
    LOVE_PROPENSITY='Love propensity',
    LUST_PROPENSITY='Lust propensity',
    ORDERLINESS='Orderliness',
    PERFECTIONIST='Perfectionism',
    PERSEVERANCE='Perseverance',
    POLITENESS='Politeness',
    PRIDE='Pride',
    PRIVACY='Privacy',
    SINGLEMINDED='Single-mindedness',
    STRESS_VULNERABILITY='Stress vulnerability',
    SWAYED_BY_EMOTIONS='Influence of emotions',
    THOUGHTLESSNESS='Thoughtlessness',
    TOLERANT='Tolerance',
    TRUST='Trust',
    VANITY='Vanity',
    VENGEFUL='Vengefulness',
    VIOLENT='Violence',
    WASTEFULNESS='Wastefulness',
}

local function unknown(kind, token)
    return {
        schema_version=1,
        kind=kind,
        known=false,
        text=('Unknown %s token: %s'):format(kind, token),
        raw=token,
        source='unknown',
        confidence='none',
    }
end

local function describe(labels, kind, token)
    local text = labels[token]
    if not text then
        return unknown(kind, token)
    end

    return {
        schema_version=1,
        kind=kind,
        known=true,
        text=text,
        raw=token,
        source='glossary',
        confidence='high',
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
