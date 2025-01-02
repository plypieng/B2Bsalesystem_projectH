# views/dashboard.py
from flask import Blueprint, render_template, flash, current_app
from flask_login import login_required, current_user
from models import db, SalesVoucherGroup, SalesB2BC, Booking, Branch
from sqlalchemy import func
from datetime import datetime, timedelta
import traceback

dashboard_bp = Blueprint('dashboard', __name__, template_folder='dashboard')

@dashboard_bp.route('/')
@login_required
def dashboard():
    try:
        # --------------------------------------------------------------------------------
        # 1) Date & Time Setup
        # --------------------------------------------------------------------------------
        today = datetime.utcnow().date()
        start_month = today.replace(day=1)       # First day of the current month
        start_year = today.replace(month=1, day=1)  # First day of the current year
        start_week = today - timedelta(days=today.weekday())
        last_30_days = today - timedelta(days=30)

        # --------------------------------------------------------------------------------
        # 2) Helper Queries For Summations
        # --------------------------------------------------------------------------------
        def voucher_sum_filter():
            """Base query to sum 'SalesVoucherGroup.total_sale' with optional branch filter."""
            q = db.session.query(func.sum(SalesVoucherGroup.total_sale))
            if current_user.role != 'admin':
                q = q.filter(SalesVoucherGroup.branch_id == current_user.branch_id)
            return q

        def b2bc_sum_filter():
            """Base query to sum 'SalesB2BC.price' with optional branch filter."""
            q = db.session.query(func.sum(SalesB2BC.price))
            if current_user.role != 'admin':
                q = q.filter(SalesB2BC.branch_id == current_user.branch_id)
            return q

        # --------------------------------------------------------------------------------
        # 3) Total Revenue: Today, This Month, This Year
        # --------------------------------------------------------------------------------
        # Today
        voucher_today = voucher_sum_filter()\
            .filter(SalesVoucherGroup.sale_date >= datetime.combine(today, datetime.min.time()),
                    SalesVoucherGroup.sale_date <= datetime.combine(today, datetime.max.time()))\
            .scalar() or 0
        b2bc_today = b2bc_sum_filter()\
            .filter(SalesB2BC.sale_date >= datetime.combine(today, datetime.min.time()),
                    SalesB2BC.sale_date <= datetime.combine(today, datetime.max.time()))\
            .scalar() or 0
        total_revenue_today = voucher_today + b2bc_today

        # This Month
        voucher_month = voucher_sum_filter()\
            .filter(SalesVoucherGroup.sale_date >= datetime.combine(start_month, datetime.min.time()),
                    SalesVoucherGroup.sale_date <= datetime.combine(today, datetime.max.time()))\
            .scalar() or 0
        b2bc_month = b2bc_sum_filter()\
            .filter(SalesB2BC.sale_date >= datetime.combine(start_month, datetime.min.time()),
                    SalesB2BC.sale_date <= datetime.combine(today, datetime.max.time()))\
            .scalar() or 0
        total_revenue_month = voucher_month + b2bc_month

        # This Year
        voucher_year = voucher_sum_filter()\
            .filter(SalesVoucherGroup.sale_date >= datetime.combine(start_year, datetime.min.time()),
                    SalesVoucherGroup.sale_date <= datetime.combine(today, datetime.max.time()))\
            .scalar() or 0
        b2bc_year = b2bc_sum_filter()\
            .filter(SalesB2BC.sale_date >= datetime.combine(start_year, datetime.min.time()),
                    SalesB2BC.sale_date <= datetime.combine(today, datetime.max.time()))\
            .scalar() or 0
        total_revenue_year = voucher_year + b2bc_year

        # --------------------------------------------------------------------------------
        # 4) Bookings (Today, This Week)
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            bookings_today = Booking.query.filter_by(booking_date=today).count()
            bookings_week = Booking.query.filter(Booking.booking_date >= start_week).count()
        else:
            bookings_today = Booking.query.filter_by(booking_date=today,
                                                     branch_id=current_user.branch_id).count()
            bookings_week = Booking.query.filter(Booking.booking_date >= start_week,
                                                 Booking.branch_id == current_user.branch_id).count()

        # --------------------------------------------------------------------------------
        # 5) Commission (This Month) - B2BC Only
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            commission_month = db.session.query(func.sum(SalesB2BC.commission_amount))\
                .filter(SalesB2BC.sale_date >= datetime.combine(start_month, datetime.min.time()),
                        SalesB2BC.sale_date <= datetime.combine(today, datetime.max.time()))\
                .scalar() or 0
        else:
            commission_month = db.session.query(func.sum(SalesB2BC.commission_amount))\
                .filter(SalesB2BC.sale_date >= datetime.combine(start_month, datetime.min.time()),
                        SalesB2BC.sale_date <= datetime.combine(today, datetime.max.time()),
                        SalesB2BC.branch_id == current_user.branch_id)\
                .scalar() or 0

        # --------------------------------------------------------------------------------
        # 6) Utilization Rate (bookings_today_count vs. capacity)
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            # Sum capacities of all branches:
            branch_capacity_sum = db.session.query(func.sum(Branch.capacity)).scalar() or 0
            bookings_today_count = Booking.query.filter_by(booking_date=today).count()

            if branch_capacity_sum > 0:
                utilization_rate = (bookings_today_count / branch_capacity_sum) * 100
            else:
                utilization_rate = 0
        else:
            # Just the current user's branch:
            branch = Branch.query.get(current_user.branch_id)
            branch_capacity = branch.capacity if branch and branch.capacity else 0
            bookings_today_count = Booking.query.filter_by(
                booking_date=today,
                branch_id=current_user.branch_id
            ).count()
            if branch_capacity > 0:
                utilization_rate = (bookings_today_count / branch_capacity) * 100
            else:
                utilization_rate = 0

        # --------------------------------------------------------------------------------
        # 7) Sales Breakdown (voucher vs. group) from SalesVoucherGroup
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            sales_breakdown = db.session.query(
                SalesVoucherGroup.sale_type,
                func.count(SalesVoucherGroup.id)
            ).group_by(SalesVoucherGroup.sale_type).all()
        else:
            sales_breakdown = db.session.query(
                SalesVoucherGroup.sale_type,
                func.count(SalesVoucherGroup.id)
            ).filter(SalesVoucherGroup.branch_id == current_user.branch_id)\
             .group_by(SalesVoucherGroup.sale_type).all()

        # --------------------------------------------------------------------------------
        # 8) Top Selling Products (limit 5) from SalesVoucherGroup
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            top_products = db.session.query(
                SalesVoucherGroup.product_name,
                func.count(SalesVoucherGroup.id).label('count')
            ).group_by(SalesVoucherGroup.product_name)\
             .order_by(func.count(SalesVoucherGroup.id).desc()).limit(5).all()
        else:
            top_products = db.session.query(
                SalesVoucherGroup.product_name,
                func.count(SalesVoucherGroup.id).label('count')
            ).filter(SalesVoucherGroup.branch_id == current_user.branch_id)\
             .group_by(SalesVoucherGroup.product_name)\
             .order_by(func.count(SalesVoucherGroup.id).desc()).limit(5).all()

        # --------------------------------------------------------------------------------
        # 9) Top Partners (limit 5) from SalesVoucherGroup
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            top_partners = db.session.query(
                SalesVoucherGroup.partner_name,
                func.sum(SalesVoucherGroup.total_sale).label('total')
            ).group_by(SalesVoucherGroup.partner_name)\
             .order_by(func.sum(SalesVoucherGroup.total_sale).desc()).limit(5).all()
        else:
            top_partners = db.session.query(
                SalesVoucherGroup.partner_name,
                func.sum(SalesVoucherGroup.total_sale).label('total')
            ).filter(SalesVoucherGroup.branch_id == current_user.branch_id)\
             .group_by(SalesVoucherGroup.partner_name)\
             .order_by(func.sum(SalesVoucherGroup.total_sale).desc()).limit(5).all()

        # --------------------------------------------------------------------------------
        # 10) Sales Trends (last 30 days): Merge Voucher & B2BC
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            vtrend = db.session.query(
                func.date(SalesVoucherGroup.sale_date).label('d'),
                func.sum(SalesVoucherGroup.total_sale).label('amt')
            ).filter(SalesVoucherGroup.sale_date >= datetime.combine(last_30_days, datetime.min.time()))\
             .group_by(func.date(SalesVoucherGroup.sale_date)).all()

            btrend = db.session.query(
                func.date(SalesB2BC.sale_date).label('d'),
                func.sum(SalesB2BC.price).label('amt')
            ).filter(SalesB2BC.sale_date >= datetime.combine(last_30_days, datetime.min.time()))\
             .group_by(func.date(SalesB2BC.sale_date)).all()
        else:
            vtrend = db.session.query(
                func.date(SalesVoucherGroup.sale_date).label('d'),
                func.sum(SalesVoucherGroup.total_sale).label('amt')
            ).filter(SalesVoucherGroup.branch_id == current_user.branch_id,
                     SalesVoucherGroup.sale_date >= datetime.combine(last_30_days, datetime.min.time()))\
             .group_by(func.date(SalesVoucherGroup.sale_date)).all()

            btrend = db.session.query(
                func.date(SalesB2BC.sale_date).label('d'),
                func.sum(SalesB2BC.price).label('amt')
            ).filter(SalesB2BC.branch_id == current_user.branch_id,
                     SalesB2BC.sale_date >= datetime.combine(last_30_days, datetime.min.time()))\
             .group_by(func.date(SalesB2BC.sale_date)).all()

        # Combine them:
        trend_dict = {}
        for row in vtrend:
            trend_dict[row.d] = trend_dict.get(row.d, 0) + (row.amt or 0)
        for row in btrend:
            trend_dict[row.d] = trend_dict.get(row.d, 0) + (row.amt or 0)
        # Sort by date:
        sales_trend = sorted(trend_dict.items(), key=lambda x: x[0])

        # --------------------------------------------------------------------------------
        # 11) Booking Trends (last 30 days)
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            bookings_trend = db.session.query(
                func.date(Booking.booking_date),
                func.count(Booking.id)
            ).filter(Booking.booking_date >= last_30_days)\
             .group_by(func.date(Booking.booking_date)).all()
        else:
            bookings_trend = db.session.query(
                func.date(Booking.booking_date),
                func.count(Booking.id)
            ).filter(Booking.branch_id == current_user.branch_id,
                     Booking.booking_date >= last_30_days)\
             .group_by(func.date(Booking.booking_date)).all()

        # --------------------------------------------------------------------------------
        # 12) Upcoming Bookings
        # --------------------------------------------------------------------------------
        if current_user.role == 'admin':
            upcoming_bookings = Booking.query.filter(Booking.booking_date >= today)\
                .order_by(Booking.booking_date, Booking.time_slot).all()
        else:
            upcoming_bookings = Booking.query.filter(Booking.branch_id == current_user.branch_id,
                                                     Booking.booking_date >= today)\
                .order_by(Booking.booking_date, Booking.time_slot).all()

        # --------------------------------------------------------------------------------
        # 13) Commission & Profit Overview
        # --------------------------------------------------------------------------------
        # Gross = sum of all voucher + B2BC
        # Commission = sum of B2BC commission_amount
        # Net = gross - commission
        if current_user.role == 'admin':
            voucher_sum_all = db.session.query(func.sum(SalesVoucherGroup.total_sale)).scalar() or 0
            b2bc_sum_all = db.session.query(func.sum(SalesB2BC.price)).scalar() or 0
            total_commission = db.session.query(func.sum(SalesB2BC.commission_amount)).scalar() or 0
        else:
            voucher_sum_all = db.session.query(func.sum(SalesVoucherGroup.total_sale))\
                .filter(SalesVoucherGroup.branch_id == current_user.branch_id).scalar() or 0
            b2bc_sum_all = db.session.query(func.sum(SalesB2BC.price))\
                .filter(SalesB2BC.branch_id == current_user.branch_id).scalar() or 0
            total_commission = db.session.query(func.sum(SalesB2BC.commission_amount))\
                .filter(SalesB2BC.branch_id == current_user.branch_id).scalar() or 0

        gross_revenue = voucher_sum_all + b2bc_sum_all
        net_revenue = gross_revenue - total_commission

        # --------------------------------------------------------------------------------
        # 14) Branch Comparisons (Revenue, Bookings)
        # --------------------------------------------------------------------------------
        # We'll merge voucher & b2bc revenue into a single 'branch_revenue'.
        if current_user.role == 'admin':
            # Vouchers by branch:
            br_voucher = db.session.query(
                Branch.name,
                func.sum(SalesVoucherGroup.total_sale).label('revenue')
            ).join(SalesVoucherGroup, SalesVoucherGroup.branch_id == Branch.id)\
             .group_by(Branch.name).all()

            # B2BC by branch:
            br_b2bc = db.session.query(
                Branch.name,
                func.sum(SalesB2BC.price).label('revenue')
            ).join(SalesB2BC, SalesB2BC.branch_id == Branch.id)\
             .group_by(Branch.name).all()

            # Bookings by branch:
            br_bookings = db.session.query(
                Branch.name,
                func.count(Booking.id).label('bookings')
            ).join(Booking, Booking.branch_id == Branch.id)\
             .group_by(Branch.name).all()
        else:
            # Restrict to current_user.branch_id
            user_branch_id = current_user.branch_id
            br_voucher = db.session.query(
                Branch.name,
                func.sum(SalesVoucherGroup.total_sale).label('revenue')
            ).join(SalesVoucherGroup, SalesVoucherGroup.branch_id == Branch.id)\
             .filter(Branch.id == user_branch_id)\
             .group_by(Branch.name).all()

            br_b2bc = db.session.query(
                Branch.name,
                func.sum(SalesB2BC.price).label('revenue')
            ).join(SalesB2BC, SalesB2BC.branch_id == Branch.id)\
             .filter(Branch.id == user_branch_id)\
             .group_by(Branch.name).all()

            br_bookings = db.session.query(
                Branch.name,
                func.count(Booking.id).label('bookings')
            ).join(Booking, Booking.branch_id == Branch.id)\
             .filter(Branch.id == user_branch_id)\
             .group_by(Branch.name).all()

        # Merge voucher & b2bc revenue
        voucher_dict = {row[0]: (row[1] or 0) for row in br_voucher}
        b2bc_dict = {row[0]: (row[1] or 0) for row in br_b2bc}

        merged_branch_revenue = {}
        all_branch_names = set(voucher_dict.keys()) | set(b2bc_dict.keys())
        for bn in all_branch_names:
            merged_branch_revenue[bn] = voucher_dict.get(bn, 0) + b2bc_dict.get(bn, 0)

        # Convert to list for the template
        branch_revenue = [(bn, merged_branch_revenue[bn]) for bn in sorted(merged_branch_revenue.keys())]
        branch_bookings = [(row[0], row[1]) for row in br_bookings]

        # --------------------------------------------------------------------------------
        # 15) Finally, Render the Template
        # --------------------------------------------------------------------------------
        return render_template('dashboard.html',
            # KPI Cards
            total_revenue_today = total_revenue_today,
            total_revenue_month = total_revenue_month,
            total_revenue_year  = total_revenue_year,
            commission_month    = commission_month,
            bookings_today      = bookings_today,
            bookings_week       = bookings_week,
            utilization_rate    = utilization_rate,
            # Charts Data
            sales_breakdown     = sales_breakdown,  # (voucher vs. group count)
            top_products        = top_products,
            top_partners        = top_partners,
            sales_trend         = sales_trend,      # combined voucher + b2bc
            bookings_trend      = bookings_trend,   # from Bookings table
            # Commission & Profit
            gross_revenue       = gross_revenue,
            total_commission    = total_commission,
            net_revenue         = net_revenue,
            # Branch Comparisons
            branch_revenue      = branch_revenue,
            branch_bookings     = branch_bookings,
            # Upcoming Bookings List
            upcoming_bookings   = upcoming_bookings
        )

    except Exception as e:
        # Capture the entire traceback
        tb = traceback.format_exc()
        # Log error to console/logs
        current_app.logger.error(f"Error in dashboard route: {e}")
        # Log the full traceback for debugging
        current_app.logger.error(f"Traceback:\n{tb}")
        # Show user-friendly message
        flash(f"An error occurred while loading the dashboard: {e}", "danger")
        # Render 500 template
        return render_template("500.html"), 500
