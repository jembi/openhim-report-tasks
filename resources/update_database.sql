use interoperability_layer;

create table alerts (
	id int PRIMARY KEY NOT NULL AUTO_INCREMENT,
	sent_date timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	message text
) CHARSET=UTF8;

alter table alerts add index `sent_date` (`sent_date`);
