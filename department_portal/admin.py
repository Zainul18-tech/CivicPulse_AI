from django.contrib import admin

from .models import (
    Department,
    DepartmentProfile,
    DepartmentTeam,
    WorkRecord,
    WorkUpdate,
)

admin.site.register(Department)
admin.site.register(DepartmentProfile)
admin.site.register(DepartmentTeam)
admin.site.register(WorkRecord)
admin.site.register(WorkUpdate)
