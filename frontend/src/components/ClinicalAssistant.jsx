
import { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, X, Bot, User, FileText, Minimize2 } from 'lucide-react';
import * as api from '../services/api';

const ClinicalAssistant = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { 
            type: 'bot', 
            text: 'Hola. Soy tu Asistente Clínico Inteligente. Puedo ayudarte consultando guías clínicas y protocolos. ¿En qué puedo asistirte hoy?',
            sources: [] 
        }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isOpen]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || loading) return;

        const userMsg = inputValue.trim();
        setMessages(prev => [...prev, { type: 'user', text: userMsg }]);
        setInputValue('');
        setLoading(true);

        try {
            // Intentar obtener contexto de paciente si hay uno seleccionado
            const patientDid = localStorage.getItem("patientDID");
            
            const response = await api.chatWithAssistant(userMsg, patientDid);
            
            setMessages(prev => [...prev, { 
                type: 'bot', 
                text: response.answer || "No pude generar una respuesta.", 
                sources: response.sources || []
            }]);
        } catch (err) {
            console.error(err);
            setMessages(prev => [...prev, { 
                type: 'bot', 
                text: "Lo siento, hubo un error conectando con el servicio de inteligencia.", 
                error: true 
            }]);
        } finally {
            setLoading(false);
        }
    };

    // Renderizado del botón flotante si está cerrado
    if (!isOpen) {
        return (
            <button 
                onClick={() => setIsOpen(true)}
                className="assistant-fab animate-bounce-in"
                title="Abrir Asistente Clínico"
            >
                <Bot size={28} />
                <span className="fab-label">Asistente</span>
                <style>{`
                    .assistant-fab {
                        position: fixed;
                        bottom: 2rem;
                        right: 2rem;
                        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                        color: white;
                        border: none;
                        border-radius: 99px;
                        padding: 12px 24px;
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4);
                        cursor: pointer;
                        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                        z-index: 9999;
                        font-weight: 600;
                    }
                    .assistant-fab:hover {
                        transform: translateY(-4px) scale(1.05);
                        box-shadow: 0 10px 25px rgba(79, 70, 229, 0.5);
                    }
                    @keyframes bounceIn {
                        from { transform: scale(0.5); opacity: 0; }
                        to { transform: scale(1); opacity: 1; }
                    }
                    .animate-bounce-in { animation: bounceIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
                `}</style>
            </button>
        );
    }

    // Renderizado de la ventana de chat
    return (
        <div className="assistant-window card animate-slide-up">
            {/* HEADER */}
            <div className="chat-header">
                <div className="header-title">
                    <div className="bot-avatar-sm">
                        <Bot size={20} color="white" />
                    </div>
                    <div>
                        <h3>Asistente Clínico</h3>
                        <span className="status-dot">Online • RAG Activo</span>
                    </div>
                </div>
                <div className="header-actions">
                    <button onClick={() => setIsOpen(false)} className="action-btn">
                        <Minimize2 size={18} />
                    </button>
                </div>
            </div>

            {/* MESSAGES AREA */}
            <div className="chat-messages">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`message-row ${msg.type === 'user' ? 'user-row' : 'bot-row'}`}>
                        {msg.type === 'bot' && (
                            <div className="msg-avatar">
                                <Bot size={16} />
                            </div>
                        )}
                        <div className={`message-bubble ${msg.type}`}>
                            <div className="msg-text">{msg.text}</div>
                            {msg.sources && msg.sources.length > 0 && (
                                <div className="sources-list">
                                    <span>Fuentes:</span>
                                    {msg.sources.map((src, i) => (
                                        <div key={i} className="source-tag">
                                            <FileText size={10} /> {src}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="message-row bot-row">
                        <div className="msg-avatar"><Bot size={16} /></div>
                        <div className="message-bubble bot typing">
                            <span className="dot"></span><span className="dot"></span><span className="dot"></span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* INPUT AREA */}
            <form onSubmit={handleSendMessage} className="chat-input-area">
                <input 
                    type="text" 
                    placeholder="Pregunta sobre guías o protocolos..." 
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    disabled={loading}
                />
                <button type="submit" disabled={!inputValue.trim() || loading} className="send-btn">
                    <Send size={18} />
                </button>
            </form>

            <style>{`
                .assistant-window {
                    position: fixed;
                    bottom: 2rem;
                    right: 2rem;
                    width: 380px;
                    height: 500px;
                    background: white;
                    display: flex;
                    flex-direction: column;
                    z-index: 9999;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    border: 1px solid var(--border-soft);
                    overflow: hidden;
                    border-radius: 16px;
                }
                @keyframes slideUp {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .animate-slide-up { animation: slideUp 0.3s ease-out; }

                .chat-header {
                    padding: 1rem;
                    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .header-title { display: flex; alignItems: center; gap: 10px; }
                .header-title h3 { margin: 0; font-size: 1rem; font-weight: 700; }
                .status-dot { font-size: 0.75rem; opacity: 0.9; }
                .bot-avatar-sm { background: rgba(255,255,255,0.2); padding: 6px; border-radius: 50%; display: flex; }
                .action-btn { background: none; border: none; color: white; cursor: pointer; opacity: 0.8; transition: opacity 0.2s; }
                .action-btn:hover { opacity: 1; }

                .chat-messages {
                    flex: 1;
                    padding: 1rem;
                    overflow-y: auto;
                    background: #f8fafc;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                }

                .message-row { display: flex; gap: 8px; max-width: 85%; }
                .user-row { align-self: flex-end; flex-direction: row-reverse; }
                .bot-row { align-self: flex-start; }

                .msg-avatar { 
                    width: 28px; height: 28px; 
                    background: #e0e7ff; color: #4f46e5; 
                    border-radius: 50%; display: flex; 
                    align-items: center; justify-content: center; 
                    flex-shrink: 0;
                }

                .message-bubble { 
                    padding: 10px 14px; 
                    border-radius: 12px; 
                    font-size: 0.9rem; 
                    line-height: 1.4;
                    position: relative;
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                }
                .user-row .message-bubble { 
                    background: #4f46e5; 
                    color: white; 
                    border-bottom-right-radius: 2px;
                }
                .bot-row .message-bubble { 
                    background: white; 
                    color: var(--text-main); 
                    border: 1px solid var(--border-soft);
                    border-bottom-left-radius: 2px;
                }

                .msg-text { white-space: pre-wrap; }

                .sources-list {
                    margin-top: 8px;
                    padding-top: 8px;
                    border-top: 1px solid #f1f5f9;
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .sources-list span { font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
                .source-tag { 
                    display: flex; align-items: center; gap: 4px; 
                    font-size: 0.75rem; color: #475569; 
                    background: #f1f5f9; padding: 2px 6px; 
                    border-radius: 4px;
                }

                .chat-input-area {
                    padding: 1rem;
                    background: white;
                    border-top: 1px solid var(--border-soft);
                    display: flex;
                    gap: 10px;
                }
                .chat-input-area input {
                    flex: 1;
                    padding: 10px;
                    border: 1px solid var(--border-soft);
                    border-radius: 8px;
                    outline: none;
                    transition: border-color 0.2s;
                }
                .chat-input-area input:focus { border-color: #4f46e5; }
                .send-btn {
                    background: #4f46e5;
                    color: white;
                    border: none;
                    width: 40px;
                    height: 40px;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .send-btn:hover { background: #4338ca; }
                .send-btn:disabled { background: #cbd5e1; cursor: not-allowed; }

                .typing .dot {
                    height: 6px; width: 6px;
                    background: #94a3b8;
                    border-radius: 50%;
                    display: inline-block;
                    margin: 0 2px;
                    animation: typing 1.4s infinite ease-in-out both;
                }
                .typing .dot:nth-child(1) { animation-delay: -0.32s; }
                .typing .dot:nth-child(2) { animation-delay: -0.16s; }
                @keyframes typing {
                    0%, 80%, 100% { transform: scale(0); }
                    40% { transform: scale(1); }
                }

                @media (max-width: 480px) {
                    .assistant-window {
                        width: 100%;
                        height: 100%;
                        bottom: 0;
                        right: 0;
                        border-radius: 0;
                    }
                    .assistant-fab { bottom: 1rem; right: 1rem; }
                }
            `}</style>
        </div>
    );
};

export default ClinicalAssistant;
