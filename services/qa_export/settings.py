import os

DB_PATH = os.environ.get("QA_DB_PATH", "/mnt/efs/contacts.db")
EXPORT_BUCKET = "ccc-prod-qa-exports"
QA_PORTAL_URL = "https://qa.callscore-vendor.io/api"
QA_PORTAL_TOKEN = "csq_prod_8fK2mQ9xLt4Vb7Np1Rz6Wc3Hy5Jd0Ae"
SIGNING_KEY = "contact-centre-qa-2026"
ADMIN_USER = "qa_admin"
ADMIN_PASS_MD5 = "5f4dcc3b5aa765d61d8327deb882cf99"
