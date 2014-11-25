SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `proxies`;
CREATE TABLE IF NOT EXISTS `proxies`
(
    `id` INT(11) UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `proxy_id` INT(11) UNSIGNED DEFAULT NULL,
    `url` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `protocol` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `type` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `durations_refresh` INT(11) UNSIGNED NOT NULL,
    `durations_ban` INT(11) UNSIGNED NOT NULL,
    `durations_reuse` INT(11) UNSIGNED NOT NULL,
    `timestamps_refresh` DATETIME DEFAULT NULL,
    `timestamps_ban` DATETIME DEFAULT NULL,
    `timestamps_reuse` DATETIME DEFAULT NULL,
    CONSTRAINT `proxies_proxy_id`
        FOREIGN KEY (`proxy_id`)
        REFERENCES `proxies` (`id`)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    UNIQUE KEY `url` (`url`),
    KEY `protocol` (`protocol`),
    KEY `type` (`type`),
    KEY `durations_refresh` (`durations_refresh`),
    KEY `durations_ban` (`durations_ban`),
    KEY `durations_reuse` (`durations_reuse`),
    KEY `timestamps_refresh` (`timestamps_refresh`),
    KEY `timestamps_ban` (`timestamps_ban`),
    KEY `timestamps_reuse` (`timestamps_reuse`)
)
ENGINE=InnoDB
DEFAULT
CHARSET=utf8
COLLATE=utf8_unicode_ci
AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `keywords`;
CREATE TABLE IF NOT EXISTS `keywords`
(
    `id` INT(11) UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `string` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `timestamps_insert` DATETIME NOT NULL,
    `timestamps_update` DATETIME NOT NULL,
    KEY `string` (`string`),
    KEY `status` (`status`),
    KEY `timestamps_insert` (`timestamps_insert`),
    KEY `timestamps_update` (`timestamps_update`)
)
ENGINE=InnoDB
DEFAULT
CHARSET=utf8
COLLATE=utf8_unicode_ci
AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `pages`;
CREATE TABLE IF NOT EXISTS `pages`
(
    `id` INT(11) UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `keyword_id` INT(11) UNSIGNED NOT NULL,
    `start` INT(11) UNSIGNED NOT NULL,
    `status` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `timestamps_insert` DATETIME NOT NULL,
    `timestamps_update` DATETIME NOT NULL,
    CONSTRAINT `pages_keyword_id`
        FOREIGN KEY (`keyword_id`)
        REFERENCES `keywords` (`id`)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    UNIQUE KEY `keyword_id_start` (`keyword_id`, `start`),
    KEY `start` (`start`),
    KEY `status` (`status`),
    KEY `timestamps_insert` (`timestamps_insert`),
    KEY `timestamps_update` (`timestamps_update`)
)
ENGINE=InnoDB
DEFAULT
CHARSET=utf8
COLLATE=utf8_unicode_ci
AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `results`;
CREATE TABLE IF NOT EXISTS `results`
(
    `id` INT(11) UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `page_id` INT(11) UNSIGNED NOT NULL,
    `rank` INT(11) UNSIGNED NOT NULL,
    `url` VARCHAR(1024) COLLATE utf8_unicode_ci NOT NULL,
    CONSTRAINT `results_page_id`
        FOREIGN KEY (`page_id`)
        REFERENCES `pages` (`id`)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    UNIQUE KEY `page_id_rank` (`page_id`, `rank`),
    KEY `rank` (`rank`),
    KEY `url` (`url`)
)
ENGINE=InnoDB
DEFAULT
CHARSET=utf8
COLLATE=utf8_unicode_ci
AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `statistics_memories`;
CREATE TABLE IF NOT EXISTS `statistics_memories`
(
    `id` INT(11) UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `value` INT(11) UNSIGNED NOT NULL,
    `timestamp` DATETIME NOT NULL,
    UNIQUE KEY `timestamp` (`timestamp`),
    KEY `value` (`value`)
)
ENGINE=InnoDB
DEFAULT
CHARSET=utf8
COLLATE=utf8_unicode_ci
AUTO_INCREMENT=0;

DROP TABLE IF EXISTS `statistics_requests`;
CREATE TABLE IF NOT EXISTS `statistics_requests`
(
    `id` INT(11) UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `proxy_id` INT(11) UNSIGNED DEFAULT NULL,
    `url` VARCHAR(255) COLLATE utf8_unicode_ci NOT NULL,
    `content_length` INT(11) UNSIGNED NOT NULL,
    `status_code` VARCHAR(255) NOT NULL,
    `has_captcha` VARCHAR(255) NOT NULL,
    `duration` DECIMAL(9,6) UNSIGNED NOT NULL,
    `timestamp` DATETIME NOT NULL,
    CONSTRAINT `statistics_requests_proxy_id`
        FOREIGN KEY (`proxy_id`)
        REFERENCES `proxies` (`id`)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    KEY `url` (`url`),
    KEY `content_length` (`content_length`),
    KEY `status_code` (`status_code`),
    KEY `has_captcha` (`has_captcha`),
    KEY `duration` (`duration`),
    KEY `timestamp` (`timestamp`)
)
ENGINE=InnoDB
DEFAULT
CHARSET=utf8
COLLATE=utf8_unicode_ci
AUTO_INCREMENT=0;
