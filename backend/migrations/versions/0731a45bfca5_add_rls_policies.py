"""add_rls_policies

Revision ID: 0731a45bfca5
Revises: f9b5f87f0cb2
Create Date: 2026-01-16 08:11:31.094143

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '0731a45bfca5'
down_revision: Union[str, Sequence[str], None] = 'f9b5f87f0cb2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable Row Level Security on all tables and create access policies."""
    # Enable RLS on all tables
    op.execute("ALTER TABLE problems ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE problem_languages ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE test_cases ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_progress ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_code ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY")

    # Shared content policies (SELECT only for authenticated users)
    op.execute('''
        CREATE POLICY "Authenticated users can read problems"
        ON problems FOR SELECT TO authenticated USING (true)
    ''')
    op.execute('''
        CREATE POLICY "Authenticated users can read problem_languages"
        ON problem_languages FOR SELECT TO authenticated USING (true)
    ''')
    op.execute('''
        CREATE POLICY "Authenticated users can read test_cases"
        ON test_cases FOR SELECT TO authenticated USING (true)
    ''')

    # user_progress policies
    op.execute('''
        CREATE POLICY "Users can view own progress"
        ON user_progress FOR SELECT TO authenticated
        USING (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can insert own progress"
        ON user_progress FOR INSERT TO authenticated
        WITH CHECK (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can update own progress"
        ON user_progress FOR UPDATE TO authenticated
        USING (user_id = auth.uid()::text)
        WITH CHECK (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can delete own progress"
        ON user_progress FOR DELETE TO authenticated
        USING (user_id = auth.uid()::text)
    ''')

    # submissions policies (immutable - no UPDATE/DELETE)
    op.execute('''
        CREATE POLICY "Users can view own submissions"
        ON submissions FOR SELECT TO authenticated
        USING (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can insert own submissions"
        ON submissions FOR INSERT TO authenticated
        WITH CHECK (user_id = auth.uid()::text)
    ''')

    # user_code policies
    op.execute('''
        CREATE POLICY "Users can view own saved code"
        ON user_code FOR SELECT TO authenticated
        USING (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can insert own saved code"
        ON user_code FOR INSERT TO authenticated
        WITH CHECK (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can update own saved code"
        ON user_code FOR UPDATE TO authenticated
        USING (user_id = auth.uid()::text)
        WITH CHECK (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can delete own saved code"
        ON user_code FOR DELETE TO authenticated
        USING (user_id = auth.uid()::text)
    ''')

    # chat_sessions policies
    op.execute('''
        CREATE POLICY "Users can view own chat sessions"
        ON chat_sessions FOR SELECT TO authenticated
        USING (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can create own chat sessions"
        ON chat_sessions FOR INSERT TO authenticated
        WITH CHECK (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can update own chat sessions"
        ON chat_sessions FOR UPDATE TO authenticated
        USING (user_id = auth.uid()::text)
        WITH CHECK (user_id = auth.uid()::text)
    ''')
    op.execute('''
        CREATE POLICY "Users can delete own chat sessions"
        ON chat_sessions FOR DELETE TO authenticated
        USING (user_id = auth.uid()::text)
    ''')

    # chat_messages policies (via session ownership)
    op.execute('''
        CREATE POLICY "Users can view messages in own sessions"
        ON chat_messages FOR SELECT TO authenticated
        USING (EXISTS (
            SELECT 1 FROM chat_sessions
            WHERE chat_sessions.id = chat_messages.session_id
            AND chat_sessions.user_id = auth.uid()::text
        ))
    ''')
    op.execute('''
        CREATE POLICY "Users can insert messages in own sessions"
        ON chat_messages FOR INSERT TO authenticated
        WITH CHECK (EXISTS (
            SELECT 1 FROM chat_sessions
            WHERE chat_sessions.id = chat_messages.session_id
            AND chat_sessions.user_id = auth.uid()::text
        ))
    ''')
    op.execute('''
        CREATE POLICY "Users can delete messages in own sessions"
        ON chat_messages FOR DELETE TO authenticated
        USING (EXISTS (
            SELECT 1 FROM chat_sessions
            WHERE chat_sessions.id = chat_messages.session_id
            AND chat_sessions.user_id = auth.uid()::text
        ))
    ''')


def downgrade() -> None:
    """Drop all RLS policies and disable RLS on all tables."""
    # Drop all policies (must use exact names)
    # chat_messages
    op.execute('DROP POLICY IF EXISTS "Users can delete messages in own sessions" ON chat_messages')
    op.execute('DROP POLICY IF EXISTS "Users can insert messages in own sessions" ON chat_messages')
    op.execute('DROP POLICY IF EXISTS "Users can view messages in own sessions" ON chat_messages')

    # chat_sessions
    op.execute('DROP POLICY IF EXISTS "Users can delete own chat sessions" ON chat_sessions')
    op.execute('DROP POLICY IF EXISTS "Users can update own chat sessions" ON chat_sessions')
    op.execute('DROP POLICY IF EXISTS "Users can create own chat sessions" ON chat_sessions')
    op.execute('DROP POLICY IF EXISTS "Users can view own chat sessions" ON chat_sessions')

    # user_code
    op.execute('DROP POLICY IF EXISTS "Users can delete own saved code" ON user_code')
    op.execute('DROP POLICY IF EXISTS "Users can update own saved code" ON user_code')
    op.execute('DROP POLICY IF EXISTS "Users can insert own saved code" ON user_code')
    op.execute('DROP POLICY IF EXISTS "Users can view own saved code" ON user_code')

    # submissions
    op.execute('DROP POLICY IF EXISTS "Users can insert own submissions" ON submissions')
    op.execute('DROP POLICY IF EXISTS "Users can view own submissions" ON submissions')

    # user_progress
    op.execute('DROP POLICY IF EXISTS "Users can delete own progress" ON user_progress')
    op.execute('DROP POLICY IF EXISTS "Users can update own progress" ON user_progress')
    op.execute('DROP POLICY IF EXISTS "Users can insert own progress" ON user_progress')
    op.execute('DROP POLICY IF EXISTS "Users can view own progress" ON user_progress')

    # Shared content
    op.execute('DROP POLICY IF EXISTS "Authenticated users can read test_cases" ON test_cases')
    op.execute('DROP POLICY IF EXISTS "Authenticated users can read problem_languages" ON problem_languages')
    op.execute('DROP POLICY IF EXISTS "Authenticated users can read problems" ON problems')

    # Disable RLS on all tables
    op.execute("ALTER TABLE chat_messages DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE chat_sessions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_code DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submissions DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_progress DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE test_cases DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE problem_languages DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE problems DISABLE ROW LEVEL SECURITY")
