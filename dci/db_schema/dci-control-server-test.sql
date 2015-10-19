INSERT INTO teams (id, name) VALUES ('3819e401-3472-4ccb-8c3e-35cbf1185dbf', 'admin');
INSERT INTO teams (id, name) VALUES ('4819e401-3472-4ccb-8c3e-35cbf1185dbf', 'company_a');
INSERT INTO teams (id, name) VALUES ('5819e401-3472-4ccb-8c3e-35cbf1185dbf', 'company_b');

INSERT INTO users (id, name, password, team_id)
VALUES ('6819e401-3472-4ccb-8c3e-35cbf1185dbf','admin', crypt('admin', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE name='company_a'));

INSERT INTO users (id, name, password, team_id)
VALUES ('7819e401-3472-4ccb-8c3e-35cbf1185dbf', 'company_a_user', crypt('company_a_user', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE name='company_a'));

INSERT INTO users (id, name, password, team_id)
VALUES ('8819e401-3472-4ccb-8c3e-35cbf1185dbf', 'company_b_user', crypt('company_b_user', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE NAME='company_b'));

INSERT INTO roles (id, name) VALUES ('9819e401-3472-4ccb-8c3e-35cbf1185dbf', 'admin');
INSERT INTO roles (id, name) VALUES ('5919e401-3472-4ccb-8c3e-35cbf1185dbf', 'partner');

INSERT INTO user_roles (id, user_id, role_id)
VALUES ('5a19e401-3472-4ccb-8c3e-35cbf1185dbf', (SELECT id FROM users WHERE name='admin'),
        (SELECT id FROM roles WHERE name='admin'));

INSERT INTO user_roles (id, user_id, role_id)
VALUES ('5b19e401-3472-4ccb-8c3e-35cbf1185dbf', (SELECT id FROM users WHERE name='admin'),
        (SELECT id from roles WHERE name='partner'));

insert into user_roles (id, user_id, role_id)
values ('5c19e401-3472-4ccb-8c3e-35cbf1185dbf', (select id from users where name='company_a_user'),
        (select id from roles where name='partner'));
insert into user_roles (id, user_id, role_id)
values ('5d19e401-3472-4ccb-8c3e-35cbf1185dbf', (select id from users where name='company_b_user'),
        (select id from roles where name='partner'));
