import logging
from dashboard.selectors import DashboardSelector
from dashboard.exceptions import DashboardDataFetchException

logger = logging.getLogger(__name__)

class DashboardService:
    @staticmethod
    def get_user_dashboard_stats(user):
        try:
            active_workspaces = DashboardSelector.get_active_workspaces_count(user)
            total_quizzes = DashboardSelector.get_total_quizzes_taken(user)
            average_accuracy = DashboardSelector.get_average_accuracy(user)
            questions_solved = DashboardSelector.get_total_questions_solved(user)
            total_study_time = DashboardSelector.get_total_study_time(user)
            study_streak = DashboardSelector.get_study_streak(user)
            recent_workspaces = DashboardSelector.get_recent_workspaces(user)
            recent_quizzes = DashboardSelector.get_recent_quizzes(user)
            upcoming_revision = DashboardSelector.get_upcoming_schedule(user)

            return {
                "active_workspaces": active_workspaces,
                "total_quizzes_taken": total_quizzes,
                "average_accuracy": round(float(average_accuracy), 2),
                "questions_solved": questions_solved,
                "total_study_time": total_study_time,
                "study_streak": study_streak,
                "recent_workspaces": recent_workspaces,
                "recent_quizzes": recent_quizzes,
                "upcoming_revision": upcoming_revision,
            }
        except Exception as e:
            logger.error("Failed to fetch dashboard stats for user %s: %s", user.id, str(e))
            raise DashboardDataFetchException()

    @staticmethod
    def generate_weekly_graph(user):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import io
        import numpy as np

        daily_data = DashboardSelector.get_weekly_study_time_data(user)
        
        fig, ax = plt.subplots(figsize=(6, 3))
        
        ax.axis('off')
        
        x = np.arange(7)
        y = np.array(daily_data)
        
        if np.max(y) == 0:
            y = np.ones(7) * 0.1
            ax.set_ylim(0, 1)
        else:
            ax.set_ylim(0, np.max(y) * 1.2)
            
        ax.set_xlim(0, 6)
        
        line_color = '#7c3aed'
        ax.plot(x, y, color=line_color, linewidth=3)
        
        ax.fill_between(x, y, 0, color=line_color, alpha=0.2)
        
        plt.tight_layout(pad=0)
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
