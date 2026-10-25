import React, { useState, useEffect, useRef } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import EmojiPicker from './components/EmojiPicker';
import StoryDisplay from './components/StoryDisplay';

// URL relative : le proxy Nginx (/api -> api:8000) fait le travail.
// L'application fonctionne donc depuis n'importe quelle machine du réseau,
// pas seulement depuis la VM elle-même.
const API_URL = '/api';

const POLL_INTERVAL = 3000; // 3 s entre chaque vérification
const MAX_POLLS = 40;       // 40 x 3 s = 2 min maximum d'attente

function App() {
    const [allEmojis, setAllEmojis] = useState([]);
    const [randomEmojis, setRandomEmojis] = useState([]);
    const [selectedEmojis, setSelectedEmojis] = useState([]);
    const [finalSequence, setFinalSequence] = useState([]);
    const [story, setStory] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [step, setStep] = useState(1);
    const [newEmojis, setNewEmojis] = useState([]);
    const [theme, setTheme] = useState('');
    const [showGallery, setShowGallery] = useState(false);
    const [gallery, setGallery] = useState([]);
    const [emojiKeywords, setEmojiKeywords] = useState({});
    const pollRef = useRef(null);

    const stopPolling = () => {
        if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
        }
    };

    // Nettoyage si on quitte le composant
    useEffect(() => () => stopPolling(), []);

    useEffect(() => {
        fetch(`${API_URL}/emojis`)
            .then(res => res.json())
            .then(data => {
                const flat = [];
                Object.values(data.categories).forEach(cat => flat.push(...cat));
                setAllEmojis(flat);
                setEmojiKeywords(data.keywords || {});
            })
            .catch(() => setError("API injoignable. Vérifie que la stack Docker est lancée."));
        fetch(`${API_URL}/emojis/random`)
            .then(res => res.json())
            .then(data => setRandomEmojis(data.random))
            .catch(() => {});
    }, []);

    // Polling robuste : s'arrête sur "completed", sur erreur, ou au bout de 2 min
    const pollStory = (storyId) => {
        stopPolling();
        let attempts = 0;
        pollRef.current = setInterval(async () => {
            attempts++;
            try {
                const res = await fetch(`${API_URL}/stories/${storyId}`);
                if (!res.ok) throw new Error('API');
                const data = await res.json();
                setStory(data);
                if (data.status === 'completed') {
                    stopPolling();
                    setLoading(false);
                } else if (attempts >= MAX_POLLS) {
                    stopPolling();
                    setLoading(false);
                    setError("La génération prend trop de temps. Vérifie l'onglet Executions dans n8n.");
                }
            } catch (err) {
                stopPolling();
                setLoading(false);
                setError("Impossible de récupérer l'histoire (API injoignable).");
            }
        }, POLL_INTERVAL);
    };

    const openGallery = () => {
        fetch(`${API_URL}/stories`)
            .then(res => res.json())
            .then(data => setGallery(data.stories || []))
            .catch(() => setError("Impossible de charger la galerie."));
        setShowGallery(true);
    };

    const deleteStory = (storyId) => {
        if (!window.confirm('Supprimer définitivement cette histoire (texte, image et audio) ?')) return;
        fetch(`${API_URL}/stories/${storyId}`, { method: 'DELETE' })
            .then(res => {
                if (!res.ok) throw new Error('API');
                setGallery(gallery.filter(g => g.story_id !== storyId));
            })
            .catch(() => setError("Impossible de supprimer cette histoire (API injoignable ?)."));
    };

    const openStory = async (storyId) => {
        setShowGallery(false);
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/stories/${storyId}`);
            if (!res.ok) throw new Error('API');
            const data = await res.json();
            setStory(data);
            setStep(3);
            setLoading(false);
        } catch (err) {
            setLoading(false);
            setError("Impossible de charger cette histoire.");
        }
    };

    const handleSelect = (emoji) => {
        if (selectedEmojis.length < 4 && !selectedEmojis.includes(emoji)) {
            setSelectedEmojis([...selectedEmojis, emoji]);
        }
    };

    const onDragEnd = (result) => {
        if (!result.destination) return;
        const items = Array.from(finalSequence);
        const [reordered] = items.splice(result.source.index, 1);
        items.splice(result.destination.index, 0, reordered);
        setFinalSequence(items);
    };

    const handleValidateSelection = () => {
        setFinalSequence([...randomEmojis, ...selectedEmojis]);
        setStep(2);
    };

    const handleGenerateStory = async () => {
        setLoading(true);
        setError(null);
        setStep(3);
        try {
            const res = await fetch(`${API_URL}/stories`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ emojis: finalSequence, theme: theme.trim() || null })
            });
            if (!res.ok) throw new Error('API');
            const data = await res.json();
            pollStory(data.story_id);
        } catch (err) {
            setLoading(false);
            setError("Échec de la création de l'histoire. Vérifie que l'API est lancée.");
        }
    };

    const handleExtendStory = async () => {
        if (newEmojis.length === 0) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/stories/${story.story_id}/extend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_emojis: newEmojis })
            });
            if (!res.ok) throw new Error('API');
            setNewEmojis([]);
            pollStory(story.story_id);
        } catch (err) {
            setLoading(false);
            setError("Échec de l'extension de l'histoire.");
        }
    };

    return (
        <div className="app">
            <a href="https://lab-anto.com" target="_blank" rel="noreferrer" className="logo-link" title="Visiter lab-anto.com">
                <img src="/lab-anto.png" alt="Logo lab-anto" className="logo" />
            </a>
            <h1>🎭 Emoji Story Generator</h1>
            <p className="subtitle">Crée une histoire avec son environnement en évolution - un univers visuel et sonore à partir d'émoticônes !</p>

            {error && <div className="error-banner">⚠️ {error}</div>}

            <div className="topbar">
                <button className="secondary-btn small" onClick={() => window.location.reload()}>
                    🎲 Nouvelle histoire
                </button>
                <button className="secondary-btn small" onClick={openGallery}>
                    📚 Galerie
                </button>
            </div>

            {showGallery && (
                <div className="section">
                    <h2>📚 Galerie des histoires</h2>
                    <p className="hint">Clique sur une histoire pour la relire, ou sur le ✕ en haut à droite pour la supprimer.</p>
                    {gallery.length === 0 && <p>Aucune histoire créée pour le moment.</p>}
                    {gallery.map(item => (
                        <div
                            key={item.story_id}
                            className="gallery-item"
                            role="button"
                            tabIndex={0}
                            onClick={() => openStory(item.story_id)}
                            onKeyDown={(e) => { if (e.key === 'Enter') openStory(item.story_id); }}
                        >
                            <button
                                className="gallery-delete"
                                title="Supprimer cette histoire"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    deleteStory(item.story_id);
                                }}
                            >
                                ✕
                            </button>
                            <div className="gallery-emojis">{item.emojis.slice(0, 10).join(' ')}</div>
                            {item.theme && <div className="gallery-theme">🏷️ {item.theme}</div>}
                            {item.excerpt && <div className="gallery-excerpt">{item.excerpt.replace(/\*\*/g, '')}</div>}
                            <div className="gallery-meta">
                                {item.created_at ? new Date(/Z|\+/.test(item.created_at) ? item.created_at : item.created_at + 'Z').toLocaleString('fr-FR') : ''} · {item.status}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {step === 1 && (
                <>
                    <div className="section">
                        <h2>🎲 Tes 6 émoticônes aléatoires</h2>
                        <div className="random-emojis">
                            {randomEmojis.map((emoji, i) => (
                                <span key={i} className="big-emoji">{emoji}</span>
                            ))}
                        </div>
                    </div>

                    <div className="section">
                        <h2>🏷️ Thème (optionnel)</h2>
                        <p className="hint">Aventure, policier, suspense, humour, poétique, romantique… ou ton propre thème libre. Il guidera le texte et l'illustration.</p>
                        <input
                            type="text"
                            className="theme-input"
                            placeholder="Ex. : aventure pirates en territoire glacial"
                            maxLength={100}
                            value={theme}
                            onChange={(e) => setTheme(e.target.value)}
                        />
                    </div>

                    <div className="section">
                        <h2>➕ Ajoute 4 émoticônes</h2>
                        {selectedEmojis.length > 0 && (
                            <>
                                <p className="hint">Tes émoticônes choisis — clique dessus pour en retirer :</p>
                                <div className="selected-emojis">
                                    {selectedEmojis.map(e => (
                                        <button
                                            key={e}
                                            className="selected-emoji-chip"
                                            title="Retirer cet émoji"
                                            onClick={() => setSelectedEmojis(selectedEmojis.filter(x => x !== e))}
                                        >
                                            {e}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                        <EmojiPicker
                            emojis={allEmojis.filter(e => !randomEmojis.includes(e) && !selectedEmojis.includes(e))}
                            selected={selectedEmojis}
                            onSelect={handleSelect}
                            maxSelection={4}
                            keywords={emojiKeywords}
                        />
                    </div>

                    {selectedEmojis.length === 4 && (
                        <button className="primary-btn" onClick={handleValidateSelection}>
                            ✅ Valider et ordonner →
                        </button>
                    )}
                </>
            )}

            {step === 2 && (
                <>
                    <div className="section">
                        <h2>🔀 Ordonne tes 10 émoticônes</h2>
                        <p className="hint">Glisse-dépose pour créer ta séquence narrative</p>
                        <DragDropContext onDragEnd={onDragEnd}>
                            <Droppable droppableId="sequence" direction="horizontal">
                                {(provided) => (
                                    <div
                                        className="sequence-list"
                                        {...provided.droppableProps}
                                        ref={provided.innerRef}
                                    >
                                        {finalSequence.map((emoji, index) => (
                                            <Draggable key={index} draggableId={`e-${index}`} index={index}>
                                                {(dragProvided) => (
                                                    <div
                                                        className="sequence-emoji"
                                                        ref={dragProvided.innerRef}
                                                        {...dragProvided.draggableProps}
                                                        {...dragProvided.dragHandleProps}
                                                    >
                                                        <span className="num">{index + 1}</span>
                                                        <span className="emoji">{emoji}</span>
                                                    </div>
                                                )}
                                            </Draggable>
                                        ))}
                                        {provided.placeholder}
                                    </div>
                                )}
                            </Droppable>
                        </DragDropContext>
                    </div>

                    <button className="primary-btn" onClick={handleGenerateStory}>
                        📖 Générer l'histoire !
                    </button>
                </>
            )}

            {step === 3 && (
                <>
                    <StoryDisplay story={story} loading={loading} />

                    {story && story.status === 'completed' && (
                        <div className="section extend-section">
                            <h3>➕ Faire évoluer l'histoire</h3>
                            <p>Ajoute de nouveaux émoticônes pour continuer l'aventure</p>
                            <EmojiPicker
                                emojis={allEmojis.filter(e => !story.emojis.includes(e))}
                                selected={newEmojis}
                                onSelect={(e) => {
                                    if (newEmojis.includes(e)) {
                                        setNewEmojis(newEmojis.filter(x => x !== e));
                                    } else {
                                        setNewEmojis([...newEmojis, e]);
                                    }
                                }}
                                keywords={emojiKeywords}
                                allowToggle={true}
                                title="Choisis les émoticônes qui feront évoluer l'histoire :"
                            />
                            <button
                                className="primary-btn"
                                onClick={handleExtendStory}
                                disabled={newEmojis.length === 0 || loading}
                            >
                                {loading ? '⏳ Génération...' : "🔄 Évoluer l'histoire"}
                            </button>
                        </div>
                    )}

                    <button className="secondary-btn" onClick={() => window.location.reload()}>
                        🎲 Nouvelle histoire
                    </button>
                </>
            )}
        </div>
    );
}

export default App;
