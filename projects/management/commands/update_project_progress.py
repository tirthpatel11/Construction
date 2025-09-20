from django.core.management.base import BaseCommand
from django.utils import timezone
from projects.models import Project, ProjectProgressSnapshot
from engineering.models import ProjectSchedule, ScheduleActivity


class Command(BaseCommand):
    help = 'Compute and store daily project progress snapshots (EVM-based).'

    def handle(self, *args, **options):
        today = timezone.now().date()
        projects = Project.objects.all()
        created, updated = 0, 0
        for project in projects:
            schedules = ProjectSchedule.objects.filter(project=project)
            activities = ScheduleActivity.objects.filter(schedule__in=schedules)
            progress = 0.0
            spi = None
            cpi = None
            if activities.exists():
                planned_total = sum(a.duration_days for a in activities if a.duration_days > 0) or 0
                if planned_total > 0:
                    earned, planned = 0.0, 0.0
                    for a in activities:
                        duration = max(1, a.duration_days)
                        weight = duration / planned_total
                        earned += weight * (a.completion_percentage / 100.0)
                        if a.planned_start and a.planned_end:
                            total_days = max(1, (a.planned_end - a.planned_start).days)
                            if today >= a.planned_end:
                                elapsed = total_days
                            elif today <= a.planned_start:
                                elapsed = 0
                            else:
                                elapsed = (today - a.planned_start).days
                            planned += weight * min(1.0, max(0.0, elapsed / total_days))
                    progress = round(earned * 100.0, 2)
                    eps = 1e-6
                    spi = round((earned + eps) / (planned + eps), 2)
            else:
                if project.estimated_budget and project.estimated_budget > 0:
                    progress = round(min(100.0, float(project.actual_cost) / float(project.estimated_budget) * 100.0), 2)

            if project.actual_cost and project.actual_cost > 0 and project.estimated_budget and project.estimated_budget > 0:
                cpi = round(float(project.estimated_budget) / float(project.actual_cost), 2)

            snap, created_flag = ProjectProgressSnapshot.objects.update_or_create(
                project=project,
                snapshot_date=today,
                defaults={'progress_percent': progress, 'spi': spi, 'cpi': cpi}
            )
            if created_flag:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Progress snapshots - created: {created}, updated: {updated}"))






