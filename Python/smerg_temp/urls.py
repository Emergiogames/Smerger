from django.urls import path
from .views import *

urlpatterns = [
    path('login',LoginView.as_view()),
    path('user',UserView.as_view()),
    path('business',BusinessView.as_view()),
    path('business/<int:id>',BusinessView.as_view()),
    path('advisor',AdvisorView.as_view()),
    path('advisor/<int:id>',AdvisorView.as_view()),
    path('franchise',FranchiseView.as_view()),
    path('franchise/<int:id>',FranchiseView.as_view()),
    path('investor',InvestorView.as_view()),
    path('investor/<int:id>',InvestorView.as_view()),
    path('block',Blocked.as_view()),
    path('plans',Plans.as_view()),
    path('plans/<int:id>',Plans.as_view()),
    path('banner',Banners.as_view()),
    path('banner<int:id>',Banners.as_view()),
    path('notification',Notifications.as_view()),
    path('report',AdminReportView.as_view()),
    path('dashboard',DashboardView.as_view()),
    path('userconnections',Userconnections.as_view()),
    path('userconnectioncount',UserConnectionCount.as_view()),
    path('changepwd',ChangePwd.as_view()), # Change Password
    path('verify-posts', AdminPostVerification.as_view()),
    path('verify-posts/<int:id>', AdminPostVerification.as_view()),
    path('admin_create', Adminview.as_view()),
    path('admin_create/<int:id>', Adminview.as_view()),
    path('total_timespent', TotalTimeSpentView.as_view()),


]