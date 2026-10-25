import React, { useState } from 'react';

// Recherche insensible à la casse et aux accents (é -> e)
const normalize = (s) =>
    (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');

function EmojiPicker({ emojis, selected, onSelect, maxSelection, keywords, allowToggle, title }) {
    const [query, setQuery] = useState('');
    const q = normalize(query.trim());

    // Mot(s)-clé(s) d'un émoji (tolérant au sélecteur de variation \uFE0F)
    const kw = keywords || {};
    const kwFor = (e) => kw[e] || kw[e.replace(/\uFE0F/g, '')] || '';

    const visible = q
        ? emojis.filter(e => normalize(kwFor(e)).includes(q))
        : emojis;

    return (
        <div className="emoji-picker">
            <h3>
                {maxSelection
                    ? `Choisis ${maxSelection} émoticônes (${selected.length}/${maxSelection}) :`
                    : (title || 'Choisis des émoticônes :')}
            </h3>
            <input
                type="text"
                className="emoji-search"
                placeholder="🔍 Rechercher un émoji (ex. : chat, dragon, forêt, château...)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
            />
            {q && visible.length === 0 && (
                <p className="hint">Aucun émoji ne correspond à « {query.trim()} ».</p>
            )}
            <div className="emoji-grid">
                {visible.map((emoji, i) => (
                    <button
                        key={i}
                        className={`emoji-btn ${selected.includes(emoji) ? 'selected' : ''}`}
                        onClick={() => onSelect(emoji)}
                        disabled={!allowToggle && selected.includes(emoji)}
                        title={kwFor(emoji) || undefined}
                    >
                        {emoji}
                    </button>
                ))}
            </div>
        </div>
    );
}

export default EmojiPicker;
