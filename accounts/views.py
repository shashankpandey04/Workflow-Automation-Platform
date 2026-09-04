from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.core.exceptions import PermissionDenied

def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(
                request,
                "Username and password are required.",
            )
            return render(request, "accounts/login.html")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is None:
            messages.error(
                request,
                "Invalid username or password.",
            )
            return render(request, "accounts/login.html")

        if not user.is_active:
            messages.error(
                request,
                "Your account is inactive.",
            )
            return render(request, "accounts/login.html")

        login(request, user)

        return redirect("accounts:dashboard")

    return render(request, "accounts/login.html")


@login_required
def dashboard(request):
    role = request.user.role

    if role == request.user.Role.STUDENT:
        return redirect("accounts:student_dashboard")

    if role == request.user.Role.FACULTY:
        return redirect("accounts:faculty_dashboard")

    if role == request.user.Role.HOD:
        return redirect("accounts:hod_dashboard")

    if role == request.user.Role.HOS:
        return redirect("accounts:hos_dashboard")

    if role == request.user.Role.ADMIN:
        return redirect("accounts:admin_dashboard")

    logout(request)

    messages.error(
        request,
        "Your account does not have a valid system role.",
    )

    return redirect("accounts:login")

@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("accounts:login")

    return redirect("accounts:dashboard")


@login_required
def student_dashboard(request):
    if request.user.role != request.user.Role.STUDENT:
        raise PermissionDenied

    from workflows.models import WorkflowRequest

    requests = (
        WorkflowRequest.objects
        .filter(
            submitted_by=request.user,
        )
        .select_related(
            "workflow",
            "workflow__application",
            "current_step",
        )
        .order_by("-updated_at")
    )

    return render(
        request,
        "accounts/student_dashboard.html",
        {
            "user": request.user,
            "requests": requests,
        },
    )


@login_required
def faculty_dashboard(request):
    if request.user.role != request.user.Role.FACULTY:
        raise PermissionDenied

    return render(
        request,
        "accounts/faculty_dashboard.html",
        {
            "user": request.user,
        },
    )


@login_required
def hod_dashboard(request):
    if request.user.role != request.user.Role.HOD:
        raise PermissionDenied

    return render(
        request,
        "accounts/hod_dashboard.html",
        {
            "user": request.user,
        },
    )


@login_required
def hos_dashboard(request):
    if request.user.role != request.user.Role.HOS:
        raise PermissionDenied

    return render(
        request,
        "accounts/hos_dashboard.html",
        {
            "user": request.user,
        },
    )


@login_required
def admin_dashboard(request):
    if request.user.role != request.user.Role.ADMIN:
        raise PermissionDenied

    return render(
        request,
        "accounts/admin_dashboard.html",
        {
            "user": request.user,
        },
    )