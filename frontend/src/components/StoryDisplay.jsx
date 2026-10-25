import React from 'react';

// Mini-interpréteur Markdown : Mistral produit notamment des titres en
// "**Titre**" — on les affiche en gras au lieu des astérisques brutes.
// (Split regex : seuls les paires bien formées sont converties.)
const renderInline = (text, keyPrefix) => {
    const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g).filter(Boolean);
    return parts.map((part, j) => {
        const key = `${keyPrefix}-${j}`;
        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={key}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('*') && part.endsWith('*') && part.length > 2) {
            return <em key={key}>{part.slice(1, -1)}</em>;
        }
        return <React.Fragment key={key}>{part}</React.Fragment>;
    });
};

function StoryDisplay({ story, loading }) {
    if (!story) {
        return loading ? <div className="loading">⏳ Génération de l'histoire en cours...</div> : null;
    }

    return (
        <div className="story-result">
            <h2>📜 Ton histoire</h2>
            {story.theme && <div className="story-theme">🏷️ Thème : {story.theme}</div>}
            {story.story_text ? (
                <div className="story-text">
                    {story.story_text.split('\n').map((line, i) => (
                        <React.Fragment key={i}>
                            {renderInline(line, i)}
                            {'\n'}
                        </React.Fragment>
                    ))}
                </div>
            ) : (
                <div className="loading">⏳ Mistral rédige l'histoire...</div>
            )}

            {loading && story.story_text && (
                <div className="loading small">⏳ Illustration et ambiance sonore en cours...</div>
            )}

            {story.image_url && (
                <div className="media-section">
                    <h3>🎨 Illustration</h3>
                    {/* URL relative : servie par le proxy Nginx /media/ */}
                    <img
                        src={story.image_url}
                        alt="Illustration de l'histoire"
                        className="story-image"
                    />
                </div>
            )}

            {story.audio_url && (
                <div className="media-section">
                    <h3>🔊 Ambiance sonore</h3>
                    <audio controls src={story.audio_url} />
                </div>
            )}
        </div>
    );
}

export default StoryDisplay;
