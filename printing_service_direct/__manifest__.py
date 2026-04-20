{
    "name": "Printing — Direct Service API",
    "version": "18.0.1.0.0",
    "author": "Ledo Enterprises",
    "category": "Inventory/Inventory",
    "summary": "Auto-print on stock picking validation via HTTP print service API",
    "depends": ["stock", "web"],
    "data": [
        "security/printing_service_security.xml",
        "security/ir.model.access.csv",
        "views/printing_service_views.xml",
        "views/printing_service_printer_views.xml",
        "views/printing_service_rule_views.xml",
        "views/res_menu.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
