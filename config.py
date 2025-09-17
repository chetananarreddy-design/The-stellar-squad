import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_default_secret_key'
    SUPABASE_URL = os.environ.get('SUPABASE_URL','https://bqlkskevsqurhalhszwv.supabase.co')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY','eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxbGtza2V2c3F1cmhhbGhzend2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgwODAwNjYsImV4cCI6MjA3MzY1NjA2Nn0.Gjs7GGvSqJGH0tRmWFW2p_6iAZumkz9Hp7rkbNLLA3A')
ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', 'chetananarreddy@gmail.com').split(',')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Chetana@1234')

