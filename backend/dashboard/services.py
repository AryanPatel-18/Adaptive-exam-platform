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
            ax.set_ylim(0, 1) # verticle Boundary of the chart
        else:
            ax.set_ylim(0, np.max(y) * 1.2)
            
        ax.set_xlim(0, 6) # Horizontal Boundary of the chart
        
        line_color = '#7c3aed'
        ax.plot(x, y, color=line_color, linewidth=3)
        
        ax.fill_between(x, y, 0, color=line_color, alpha=0.2)
        
        plt.tight_layout(pad=0)
        
        buf = io.BytesIO() # Creating the file and saving inside the RAM
        fig.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0) # Saving the file 
        buf.seek(0) # Moving the cursor to the beginning of the file
        plt.close(fig) # Closing the file
        
        return buf.getvalue()

    @staticmethod
    def search_workspaces(user, query):
        from workspace.models import Workspace
        from django.db.models import Q
        
        query = str(query).strip()
        if not query:
            return []
            
        # Perform ORM search across workspace title, files, quizzes, and topics
        workspaces = Workspace.objects.filter(owner=user).filter(
            Q(title__icontains=query) |
            Q(files__original_filename__icontains=query) |
            Q(quizzes__title__icontains=query) |
            Q(topics__name__icontains=query)
        ).distinct()
        
        results = []
        for ws in workspaces:
            matched_in = set()
            matched_values = set()
            
            # Check Title
            if query.lower() in ws.title.lower():
                matched_in.add("Workspace Title")
                matched_values.add(ws.title)
                
            # Check Files
            ws_files = list(ws.files.all())
            for f in ws_files:
                if query.lower() in f.original_filename.lower():
                    matched_in.add("Files")
                    matched_values.add(f.original_filename)
                    
            # Check Quizzes
            ws_quizzes = list(ws.quizzes.all())
            for q in ws_quizzes:
                if query.lower() in q.title.lower():
                    matched_in.add("Quizzes")
                    matched_values.add(q.title)
                    
            # Check Topics
            ws_topics = list(ws.topics.all())
            for t in ws_topics:
                if query.lower() in t.name.lower():
                    matched_in.add("Topics")
                    matched_values.add(t.name)
                    
            results.append({
                "workspace_id": str(ws.id),
                "workspace_title": ws.title,
                "matched_in": list(matched_in),
                "matched_values": list(matched_values)[:10],
                "content": {
                    "files": [f.original_filename for f in ws_files],
                    "topics": [t.name for t in ws_topics],
                    "quizzes": [q.title for q in ws_quizzes]
                },
                "_match_score": len(matched_in) + len(matched_values)
            })
            
        # Sort by match score and return top 3
        results.sort(key=lambda x: x["_match_score"], reverse=True)
        top_results = results[:3]
        for r in top_results:
            del r["_match_score"]
            
        return top_results

class ActivityLogger:
    @staticmethod
    def log(user, action, description, metadata=None):
        from dashboard.models import UserActivity
        try:
            UserActivity.objects.create(
                user=user,
                action=action,
                description=description,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error("Failed to log activity for user %s: %s", getattr(user, 'id', 'unknown'), str(e))
