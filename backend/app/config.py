*** Begin Patch
*** Update File: backend/app/config.py
@@
-from pydantic_settings import BaseSettings, SettingsConfigDict
-
-class Settings(BaseSettings):
-    """Central configuration. Values can be overridden via environment variables or a `.env` file.
-    """
-    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
-    # Security
-    secret_key: str = "CHANGE_ME"  # override in .env
-    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
-    # Storage
-    database_url: str = "sqlite:///./compliancebinder.db"
-    upload_dir: str = "./uploads"
-    # CORS
-    allowed_origins: str = "*"  # for MVP; lock down later
- 
-settings = Settings()
+from pydantic_settings import BaseSettings, SettingsConfigDict
+from typing import List, Optional
+import os
+
+
+class Settings(BaseSettings):
+    """Central configuration. Values can be overridden via environment variables or a `.env` file."""
+    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
+
+    # Security - MUST be overridden in production
+    secret_key: Optional[str] = None
+    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
+
+    # Storage / DB
+    database_url: str = "sqlite:///./compliancebinder.db"
+    upload_dir: str = "./uploads"
+
+    # CORS - comma-separated or JSON list in env -> parsed to list at startup
+    allowed_origins: Optional[str] = None
+
+    # Upload controls
+    max_upload_size_bytes: int = 10 * 1024 * 1024  # 10 MB default
+    allowed_content_types: List[str] = ["application/pdf", "image/png", "image/jpeg"]
+
+    def parsed_allowed_origins(self) -> List[str]:
+        if not self.allowed_origins or self.allowed_origins.strip() == "":
+            return []
+        # allow comma separated or single origin
+        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
+
+
+settings = Settings()
+
+# Fail fast: require secret key in non-dev envs
+if os.environ.get("ENV", "").lower() in ("prod", "production", "staging"):
+    if not settings.secret_key:
+        raise RuntimeError("SECRET_KEY must be set in production (env var SECRET_KEY)")
*** End Patch
