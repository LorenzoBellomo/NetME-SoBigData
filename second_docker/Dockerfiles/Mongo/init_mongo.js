db.createUser({
    user: 'netme',
    pwd: 'netme',
    roles: [
        {
            role: 'readWrite',
            db: 'netmedb',
        },
    ],
});

db = new Mongo().getDB('netmedb');
db.createCollection('dumps', { capped: false });
db.createCollection('requests', { capped: false });
db.createCollection('annotations', { capped: false });
db.createCollection('terms', { capped: false });

db.getCollection('terms').insert({
    '_id': 'bioterms', 'data': ['enhance',
        'increase',
        'induce',
        'regulate',
        'block',
        'decrease',
        'downregulate',
        'affect',
        'control',
        'cause',
        'contain',
        'detect',
        'display',
        'find',
        'reveal',
        'upregulates',
        'interacts',
        'activate',
        'associates',
        'express',
        'release',
        'trigger',
        'produce',
        'stimulate',
        'reduce',
        'ubiquitination',
        'inactivate',
        'overexpress']
});

