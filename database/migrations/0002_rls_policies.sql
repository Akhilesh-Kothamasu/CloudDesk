-- Migration: 0002_rls_policies.sql
-- Description: Enable Row Level Security and establish access policies for service_role, staff, and anon.

CREATE OR REPLACE FUNCTION auth_user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::jsonb ->> 'role',
        'viewer'
    );
EXCEPTION WHEN OTHERS THEN
    RETURN 'viewer';
END;
$$ LANGUAGE plpgsql STABLE;

-- 1. ENABLE ROW LEVEL SECURITY
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE support_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE resolution_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalations ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- 2. SERVICE ROLE POLICIES
DROP POLICY IF EXISTS "service_role_all_profiles" ON profiles;
CREATE POLICY "service_role_all_profiles" ON profiles TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_customers" ON customers;
CREATE POLICY "service_role_all_customers" ON customers TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_products" ON products;
CREATE POLICY "service_role_all_products" ON products TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_subscriptions" ON subscriptions;
CREATE POLICY "service_role_all_subscriptions" ON subscriptions TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_workspaces" ON workspaces;
CREATE POLICY "service_role_all_workspaces" ON workspaces TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_tickets" ON tickets;
CREATE POLICY "service_role_all_tickets" ON tickets TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_ticket_messages" ON ticket_messages;
CREATE POLICY "service_role_all_ticket_messages" ON ticket_messages TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_support_articles" ON support_articles;
CREATE POLICY "service_role_all_support_articles" ON support_articles TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_incidents" ON incidents;
CREATE POLICY "service_role_all_incidents" ON incidents TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_workflow_runs" ON workflow_runs;
CREATE POLICY "service_role_all_workflow_runs" ON workflow_runs TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_workflow_events" ON workflow_events;
CREATE POLICY "service_role_all_workflow_events" ON workflow_events TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_resolution_actions" ON resolution_actions;
CREATE POLICY "service_role_all_resolution_actions" ON resolution_actions TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_approval_requests" ON approval_requests;
CREATE POLICY "service_role_all_approval_requests" ON approval_requests TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_escalations" ON escalations;
CREATE POLICY "service_role_all_escalations" ON escalations TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_customer_memory" ON customer_memory;
CREATE POLICY "service_role_all_customer_memory" ON customer_memory TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_all_audit_logs" ON audit_logs;
CREATE POLICY "service_role_all_audit_logs" ON audit_logs TO service_role USING (true) WITH CHECK (true);

-- 3. AUTHENTICATED STAFF READ ACCESS
DROP POLICY IF EXISTS "staff_select_profiles" ON profiles;
CREATE POLICY "staff_select_profiles" ON profiles FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_customers" ON customers;
CREATE POLICY "staff_select_customers" ON customers FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_products" ON products;
CREATE POLICY "staff_select_products" ON products FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_subscriptions" ON subscriptions;
CREATE POLICY "staff_select_subscriptions" ON subscriptions FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_workspaces" ON workspaces;
CREATE POLICY "staff_select_workspaces" ON workspaces FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_tickets" ON tickets;
CREATE POLICY "staff_select_tickets" ON tickets FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_ticket_messages" ON ticket_messages;
CREATE POLICY "staff_select_ticket_messages" ON ticket_messages FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_support_articles" ON support_articles;
CREATE POLICY "staff_select_support_articles" ON support_articles FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_incidents" ON incidents;
CREATE POLICY "staff_select_incidents" ON incidents FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_workflow_runs" ON workflow_runs;
CREATE POLICY "staff_select_workflow_runs" ON workflow_runs FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_workflow_events" ON workflow_events;
CREATE POLICY "staff_select_workflow_events" ON workflow_events FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_resolution_actions" ON resolution_actions;
CREATE POLICY "staff_select_resolution_actions" ON resolution_actions FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_approval_requests" ON approval_requests;
CREATE POLICY "staff_select_approval_requests" ON approval_requests FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_escalations" ON escalations;
CREATE POLICY "staff_select_escalations" ON escalations FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_customer_memory" ON customer_memory;
CREATE POLICY "staff_select_customer_memory" ON customer_memory FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS "staff_select_audit_logs" ON audit_logs;
CREATE POLICY "staff_select_audit_logs" ON audit_logs FOR SELECT TO authenticated USING (true);

-- 4. AGENT & ADMIN MUTATION ACCESS
DROP POLICY IF EXISTS "agent_insert_tickets" ON tickets;
CREATE POLICY "agent_insert_tickets" ON tickets FOR INSERT TO authenticated
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_update_tickets" ON tickets;
CREATE POLICY "agent_update_tickets" ON tickets FOR UPDATE TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_insert_ticket_messages" ON ticket_messages;
CREATE POLICY "agent_insert_ticket_messages" ON ticket_messages FOR INSERT TO authenticated
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_manage_workflow_runs" ON workflow_runs;
CREATE POLICY "agent_manage_workflow_runs" ON workflow_runs FOR ALL TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_manage_workflow_events" ON workflow_events;
CREATE POLICY "agent_manage_workflow_events" ON workflow_events FOR ALL TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_manage_resolution_actions" ON resolution_actions;
CREATE POLICY "agent_manage_resolution_actions" ON resolution_actions FOR ALL TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_manage_approval_requests" ON approval_requests;
CREATE POLICY "agent_manage_approval_requests" ON approval_requests FOR ALL TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_manage_escalations" ON escalations;
CREATE POLICY "agent_manage_escalations" ON escalations FOR ALL TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_manage_customer_memory" ON customer_memory;
CREATE POLICY "agent_manage_customer_memory" ON customer_memory FOR ALL TO authenticated
    USING (auth_user_role() IN ('agent', 'admin'))
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

DROP POLICY IF EXISTS "agent_insert_audit_logs" ON audit_logs;
CREATE POLICY "agent_insert_audit_logs" ON audit_logs FOR INSERT TO authenticated
    WITH CHECK (auth_user_role() IN ('agent', 'admin'));

-- 5. ADMIN ONLY MUTATION ACCESS
DROP POLICY IF EXISTS "admin_manage_profiles" ON profiles;
CREATE POLICY "admin_manage_profiles" ON profiles FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

DROP POLICY IF EXISTS "admin_manage_customers" ON customers;
CREATE POLICY "admin_manage_customers" ON customers FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

DROP POLICY IF EXISTS "admin_manage_products" ON products;
CREATE POLICY "admin_manage_products" ON products FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

DROP POLICY IF EXISTS "admin_manage_subscriptions" ON subscriptions;
CREATE POLICY "admin_manage_subscriptions" ON subscriptions FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

DROP POLICY IF EXISTS "admin_manage_workspaces" ON workspaces;
CREATE POLICY "admin_manage_workspaces" ON workspaces FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

DROP POLICY IF EXISTS "admin_manage_support_articles" ON support_articles;
CREATE POLICY "admin_manage_support_articles" ON support_articles FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

DROP POLICY IF EXISTS "admin_manage_incidents" ON incidents;
CREATE POLICY "admin_manage_incidents" ON incidents FOR ALL TO authenticated
    USING (auth_user_role() = 'admin')
    WITH CHECK (auth_user_role() = 'admin');

-- 6. ANON READ ACCESS
DROP POLICY IF EXISTS "anon_select_support_articles" ON support_articles;
CREATE POLICY "anon_select_support_articles" ON support_articles FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "anon_select_incidents" ON incidents;
CREATE POLICY "anon_select_incidents" ON incidents FOR SELECT TO anon USING (true);

