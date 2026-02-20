import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'legally_chat_sessions';

export const useChatHistory = () => {
    const [sessions, setSessions] = useState(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved ? JSON.parse(saved) : [];
    });
    const [activeSessionId, setActiveSessionId] = useState(null);

    useEffect(() => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    }, [sessions]);

    const createNewSession = useCallback(() => {
        const newSession = {
            id: Date.now().toString(),
            title: 'Новый чат',
            messages: [],
            createdAt: new Date().toISOString(),
        };
        setSessions(prev => [newSession, ...prev]);
        setActiveSessionId(newSession.id);
        return newSession.id;
    }, []);

    const addMessageToSession = useCallback((sessionId, message) => {
        setSessions(prev => prev.map(session => {
            if (session.id === sessionId) {
                let newTitle = session.title;
                // Update title from first user message
                if (session.messages.length === 0 && message.isUser) {
                    newTitle = message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '');
                }
                return {
                    ...session,
                    title: newTitle,
                    messages: [...session.messages, message],
                };
            }
            return session;
        }));
    }, []);

    const deleteSession = useCallback((sessionId) => {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (activeSessionId === sessionId) {
            setActiveSessionId(null);
        }
    }, [activeSessionId]);

    const activeSession = sessions.find(s => s.id === activeSessionId);

    return {
        sessions,
        activeSessionId,
        setActiveSessionId,
        activeSession,
        createNewSession,
        addMessageToSession,
        deleteSession,
    };
};
