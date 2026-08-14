from flask import Blueprint, session, request, redirect, url_for, flash, render_template
from app.models.admin import PrincipalDataInfo
from app.utils.form import PrincipalDataForm
from app.extensions import db

add_principal_bp = Blueprint(
    "add_principal",
    __name__,
    url_prefix="/add_principal"
)

@add_principal_bp.route("/", methods=["GET", "POST"])
def add_principal():

    principal_data_form = PrincipalDataForm()

    if not session.get("admin"):
        return redirect(url_for("login.login"))

    try:

        if principal_data_form.validate_on_submit():
        
            principal_id = principal_data_form.principal_id.data
            first_name = principal_data_form.first_name.data
            last_name = principal_data_form.last_name.data
            mobile_number = principal_data_form.mobile_number.data
            email = principal_data_form.email.data
            institute = principal_data_form.institute.data
            institute_code = principal_data_form.institute_code.data
            username = principal_data_form.username.data
            password = principal_data_form.password.data    
        
            principal_data_info = PrincipalDataInfo(
                principal_id=principal_id,
                first_name=first_name,
                last_name=last_name,
                mobile_number=mobile_number,
                email=email,
                institute=institute,
                institute_code=institute_code,
                username=username,
                password=password
            )

            db.session.add(principal_data_info)
            db.session.commit()

            flash("Principal added successfully","success")
            return redirect(url_for("admin_dashboard.admin_dashboard"))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding principal: {e}", "danger")
        return redirect(url_for("add_principal.add_principal"))

    return render_template(
        "admin/add_principal.html",
        principal_data_form=principal_data_form
    )