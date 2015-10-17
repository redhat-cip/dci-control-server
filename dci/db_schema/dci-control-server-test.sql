INSERT INTO teams (name) VALUES ('admin');
INSERT INTO teams (name) VALUES ('company_a');
INSERT INTO teams (name) VALUES ('company_b');

INSERT INTO users (name, password, team_id)
VALUES ('admin', crypt('admin', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE name='company_a'));

INSERT INTO users (name, password, team_id)
VALUES ('company_a_user', crypt('company_a_user', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE name='company_a'));

INSERT INTO users (name, password, team_id)
VALUES ('company_b_user', crypt('company_b_user', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE NAME='company_b'));

INSERT INTO roles (name) VALUES ('admin');
INSERT INTO roles (name) VALUES ('partner');

INSERT INTO user_roles (user_id, role_id)
VALUES ((SELECT id FROM users WHERE name='admin'),
        (SELECT id FROM roles WHERE name='admin'));

INSERT INTO user_roles (user_id, role_id)
VALUES ((SELECT id FROM users WHERE name='admin'),
        (SELECT id from roles WHERE name='partner'));

insert into user_roles (user_id, role_id)
values ((select id from users where name='company_a_user'),
        (select id from roles where name='partner'));
insert into user_roles (user_id, role_id)
values ((select id from users where name='company_b_user'),
        (select id from roles where name='partner'));
