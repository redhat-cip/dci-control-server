INSERT INTO teams (name) VALUES ('admin');
INSERT INTO teams (name) VALUES ('partner');

INSERT INTO users (name, password, team_id)
VALUES ('admin', crypt('admin', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE name='partner'));

INSERT INTO users (name, password, team_id)
VALUES ('partner', crypt('partner', gen_salt('bf', 8)),
        (SELECT id FROM teams WHERE name='partner'));

INSERT INTO roles (name) VALUES ('admin');
INSERT INTO roles (name) VALUES ('partner');

INSERT INTO user_roles (user_id, role_id)
VALUES ((SELECT id FROM users WHERE name='admin'),
        (SELECT id FROM roles WHERE name='admin'));

INSERT INTO user_roles (user_id, role_id)
VALUES ((SELECT id FROM users WHERE name='admin'),
        (SELECT id from roles WHERE name='partner'));

INSERT INTO user_roles (user_id, role_id)
VALUES ((SELECT id FROM users WHERE name='partner'),
        (SELECT id FROM roles WHERE name='partner'));


