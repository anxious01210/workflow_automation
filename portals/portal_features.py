# portals/portal_features.py
def get_portal_features():
    return [
        {
            "key": "appointments",
            "label": "Appointments",
            "urlname": "portals:appointments",  # namespace = portals
            "required_perms": ["portals.appointments_view"],
            "order": 10,
            "icon": "calendar",
        },
        {
            "key": "leave",
            "label": "Leave Request",
            "urlname": "portals:leave",
            "required_perms": ["portals.leave_submit"],
            "order": 20,
            "icon": "plane",
        },
        {
            "key": "purchases",
            "label": "Purchase Request",
            "urlname": "portals:purchases",
            "required_perms": ["portals.purchase_submit"],
            "order": 30,
            "icon": "shopping-cart",
        },
    ]


# def get_portal_features():
#     return [
#         {"key": "appointments","label": "Appointments","urlname": "portals:appointments","required_perms": ["portals.appointments_view"],"order": 10},
#         {"key": "leave","label": "Leave Request","urlname": "portals:leave","required_perms": ["portals.leave_submit"],"order": 20},
#         {"key": "purchases","label": "Purchase Request","urlname": "portals:purchases","required_perms": ["portals.purchase_submit"],"order": 30},
#     ]
