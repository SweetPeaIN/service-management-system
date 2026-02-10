CREATE TABLE user (
	id INTEGER NOT NULL, 
	user_name VARCHAR(50) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password VARCHAR(30) NOT NULL, 
	address VARCHAR(100) NOT NULL, 
	contact_number VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_user_user_name ON user (user_name);
CREATE TABLE servicerequest (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	service_name VARCHAR NOT NULL, 
	status VARCHAR NOT NULL, 
	date_slot VARCHAR NOT NULL, 
	address VARCHAR NOT NULL, 
	vendor_name VARCHAR NOT NULL, 
	amount INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES user (id)
);
CREATE INDEX ix_servicerequest_customer_id ON servicerequest (customer_id);
