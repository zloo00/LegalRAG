import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import evaluationService from '../../services/evaluationService';

const ReviewerDashboard = () => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadMyTasks();
    }, []);

    const loadMyTasks = async () => {
        try {
            const response = await evaluationService.getMyTasks();
            setTasks(response.data || []);
        } catch (err) {
            console.error('Failed to load tasks', err);
            setTasks([]);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading assigned tasks...</div>;

    return (
        <div className="reviewer-dashboard">
            <header className="admin-header">
                <h1>Expert Evaluation Dashboard</h1>
                <div className="stats-mini">
                    <span className="badge status-pending">{tasks.filter(t => t.status === 'Pending').length} Pending</span>
                </div>
            </header>

            <div className="task-list">
                {(!tasks || tasks.length === 0) ? (
                    <div className="empty-state">
                        <p>No pending evaluations assigned to you at this time.</p>
                    </div>
                ) : (
                    <div className="task-grid">
                        {tasks.map(task => (
                            <div key={task.id} className="task-card" onClick={() => navigate(`/reviewer/eval/${task.id}`, { state: { task } })}>
                                <div className="task-card-header">
                                    <span className="task-id">#{task.external_id || task.id.substring(0, 8)}</span>
                                    <span className={`badge status-${task.status.toLowerCase()}`}>{task.status}</span>
                                </div>
                                <h3>{task.question}</h3>
                                <div className="task-footer">
                                    <span className="date">Assigned: {new Date(task.created_at).toLocaleDateString()}</span>
                                    <button className="eval-link">Evaluate &rarr;</button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ReviewerDashboard;
