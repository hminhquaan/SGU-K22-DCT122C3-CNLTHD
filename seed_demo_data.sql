SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS fitness_shop_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE fitness_shop_db;

DROP TABLE IF EXISTS `shop_order_item`;
DROP TABLE IF EXISTS `shop_order`;
DROP TABLE IF EXISTS `shop_cart_item`;
DROP TABLE IF EXISTS `shop_cart`;
DROP TABLE IF EXISTS `shop_product`;
DROP TABLE IF EXISTS `shop_category`;
DROP TABLE IF EXISTS `django_admin_log`;
DROP TABLE IF EXISTS `django_session`;
DROP TABLE IF EXISTS `auth_user_user_permissions`;
DROP TABLE IF EXISTS `auth_user_groups`;
DROP TABLE IF EXISTS `auth_user`;
DROP TABLE IF EXISTS `auth_group_permissions`;
DROP TABLE IF EXISTS `auth_permission`;
DROP TABLE IF EXISTS `auth_group`;
DROP TABLE IF EXISTS `django_content_type`;

CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_uniq` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_name_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_codename_uniq` (`content_type_id`, `codename`),
  KEY `auth_permission_content_type_id_idx` (`content_type_id`),
  CONSTRAINT `auth_permission_content_type_fk`
    FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_group_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_uniq` (`group_id`, `permission_id`),
  KEY `auth_group_permissions_group_id_idx` (`group_id`),
  KEY `auth_group_permissions_permission_id_idx` (`permission_id`),
  CONSTRAINT `auth_group_permissions_group_fk`
    FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `auth_group_permissions_permission_fk`
    FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_username_uniq` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_user_groups` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_uniq` (`user_id`, `group_id`),
  KEY `auth_user_groups_user_id_idx` (`user_id`),
  KEY `auth_user_groups_group_id_idx` (`group_id`),
  CONSTRAINT `auth_user_groups_user_fk`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `auth_user_groups_group_fk`
    FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `auth_user_user_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_uniq` (`user_id`, `permission_id`),
  KEY `auth_user_user_permissions_user_id_idx` (`user_id`),
  KEY `auth_user_user_permissions_permission_id_idx` (`permission_id`),
  CONSTRAINT `auth_user_user_permissions_user_fk`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `auth_user_user_permissions_permission_fk`
    FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_idx` (`content_type_id`),
  KEY `django_admin_log_user_id_idx` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_fk`
    FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
    ON DELETE SET NULL,
  CONSTRAINT `django_admin_log_user_fk`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_idx` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `shop_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `slug` varchar(140) NOT NULL,
  `description` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shop_category_name_uniq` (`name`),
  UNIQUE KEY `shop_category_slug_uniq` (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `shop_product` (
  `id` int NOT NULL AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `name` varchar(200) NOT NULL,
  `slug` varchar(220) NOT NULL,
  `price` decimal(12,2) NOT NULL,
  `image` varchar(100) NULL,
  `description` longtext NOT NULL,
  `stock` int unsigned NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shop_product_slug_uniq` (`slug`),
  KEY `shop_product_category_id_idx` (`category_id`),
  CONSTRAINT `shop_product_category_fk`
    FOREIGN KEY (`category_id`) REFERENCES `shop_category` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `shop_cart` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shop_cart_user_uniq` (`user_id`),
  CONSTRAINT `shop_cart_user_fk`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `shop_cart_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cart_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int unsigned NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shop_cart_item_uniq` (`cart_id`, `product_id`),
  KEY `shop_cart_item_cart_id_idx` (`cart_id`),
  KEY `shop_cart_item_product_id_idx` (`product_id`),
  CONSTRAINT `shop_cart_item_cart_fk`
    FOREIGN KEY (`cart_id`) REFERENCES `shop_cart` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `shop_cart_item_product_fk`
    FOREIGN KEY (`product_id`) REFERENCES `shop_product` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `shop_order` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `tracking_code` varchar(32) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) NOT NULL,
  `province` varchar(100) NOT NULL,
  `district` varchar(100) NOT NULL,
  `ward` varchar(100) NOT NULL,
  `street_address` varchar(255) NOT NULL,
  `shipping_address` longtext NOT NULL,
  `note` longtext NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `shipping_fee` decimal(12,2) NOT NULL,
  `total_amount` decimal(12,2) NOT NULL,
  `payment_method` varchar(20) NOT NULL,
  `payment_status` varchar(10) NOT NULL,
  `order_status` varchar(20) NOT NULL,
  `confirmed_at` datetime(6) NULL,
  `shipping_at` datetime(6) NULL,
  `completed_at` datetime(6) NULL,
  `cancelled_at` datetime(6) NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `shop_order_tracking_code_uniq` (`tracking_code`),
  KEY `shop_order_user_id_idx` (`user_id`),
  CONSTRAINT `shop_order_user_fk`
    FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `shop_order_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `product_id` int NULL,
  `product_name` varchar(200) NOT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  `quantity` int unsigned NOT NULL,
  `line_total` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `shop_order_item_order_id_idx` (`order_id`),
  KEY `shop_order_item_product_id_idx` (`product_id`),
  CONSTRAINT `shop_order_item_order_fk`
    FOREIGN KEY (`order_id`) REFERENCES `shop_order` (`id`)
    ON DELETE CASCADE,
  CONSTRAINT `shop_order_item_product_fk`
    FOREIGN KEY (`product_id`) REFERENCES `shop_product` (`id`)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `django_content_type` (`id`, `app_label`, `model`) VALUES
  (1, 'auth', 'permission'),
  (2, 'auth', 'group'),
  (3, 'auth', 'user'),
  (4, 'admin', 'logentry'),
  (5, 'contenttypes', 'contenttype'),
  (6, 'sessions', 'session'),
  (7, 'shop', 'category'),
  (8, 'shop', 'product'),
  (9, 'shop', 'cart'),
  (10, 'shop', 'cartitem'),
  (11, 'shop', 'order'),
  (12, 'shop', 'orderitem');

INSERT INTO `auth_user` (
  `id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`
) VALUES (
  1,
  'pbkdf2_sha256$1000000$ows2SRBAlsgsIlGQSx4n3a$C1Kq4joacimyHbpR+2ezHyV2ZCmHF+bFdP0NP6uKfF0=',
  NULL,
  1,
  'admin',
  'Zenith',
  'Admin',
  'admin@zenithfitness.local',
  1,
  1,
  '2026-05-01 08:00:00.000000'
);

INSERT INTO `shop_category` (`id`, `name`, `slug`, `description`, `is_active`, `created_at`) VALUES
  (1, 'Dụng cụ tập gym', 'dung-cu-tap-gym', 'Máy móc và phụ kiện hỗ trợ tập gym tại nhà.', 1, '2026-05-01 08:05:00.000000'),
  (2, 'Yoga', 'yoga', 'Thảm, block và dụng cụ hỗ trợ yoga, giãn cơ.', 1, '2026-05-01 08:05:00.000000'),
  (3, 'Chạy bộ', 'chay-bo', 'Phụ kiện và thiết bị cho chạy bộ, cardio.', 1, '2026-05-01 08:05:00.000000');

INSERT INTO `shop_product` (
  `id`, `category_id`, `name`, `slug`, `price`, `image`, `description`, `stock`, `is_active`, `created_at`, `updated_at`
) VALUES
  (1, 1, 'Dumbbell Adjustable Pro', 'dumbbell-adjustable-pro', 1290000.00, NULL, 'Bộ tạ tay điều chỉnh đa nấc, phù hợp tập tại nhà.', 18, 1, '2026-05-01 08:06:00.000000', '2026-05-01 08:06:00.000000'),
  (2, 1, 'Resistance Band Set', 'resistance-band-set', 390000.00, NULL, 'Bộ dây kháng lực đa mức, gọn nhẹ và linh hoạt.', 35, 1, '2026-05-01 08:06:10.000000', '2026-05-01 08:06:10.000000'),
  (3, 2, 'Premium Yoga Mat', 'premium-yoga-mat', 490000.00, NULL, 'Thảm yoga chống trượt, êm và bền cho luyện tập hằng ngày.', 22, 1, '2026-05-01 08:06:20.000000', '2026-05-01 08:06:20.000000'),
  (4, 2, 'Yoga Block Foam', 'yoga-block-foam', 150000.00, NULL, 'Gạch yoga hỗ trợ căn chỉnh tư thế và kéo giãn.', 40, 1, '2026-05-01 08:06:30.000000', '2026-05-01 08:06:30.000000'),
  (5, 3, 'Running Belt', 'running-belt', 250000.00, NULL, 'Đai chạy bộ gọn nhẹ để mang theo điện thoại và chìa khóa.', 30, 1, '2026-05-01 08:06:40.000000', '2026-05-01 08:06:40.000000'),
  (6, 3, 'Hydration Bottle', 'hydration-bottle', 180000.00, NULL, 'Bình nước thể thao tiện dụng cho chạy bộ và tập luyện.', 50, 1, '2026-05-01 08:06:50.000000', '2026-05-01 08:06:50.000000');

INSERT INTO `shop_cart` (`id`, `user_id`, `created_at`, `updated_at`) VALUES
  (1, 1, '2026-05-01 08:10:00.000000', '2026-05-01 08:10:00.000000');

INSERT INTO `shop_order` (
  `id`, `user_id`, `tracking_code`, `full_name`, `phone`, `email`, `province`, `district`, `ward`, `street_address`, `shipping_address`, `note`,
  `subtotal`, `shipping_fee`, `total_amount`, `payment_method`, `payment_status`, `order_status`,
  `confirmed_at`, `shipping_at`, `completed_at`, `cancelled_at`, `created_at`, `updated_at`
) VALUES (
  1,
  1,
  'ZF000001',
  'Admin Zenith',
  '0900000001',
  'admin@zenithfitness.local',
  'TP. Hồ Chí Minh',
  'Quận 1',
  'Bến Nghé',
  '123 Lê Lợi',
  '123 Lê Lợi, Bến Nghé, Quận 1, TP. Hồ Chí Minh',
  'Đơn mẫu để hiển thị tracking và lịch sử đơn hàng.',
  1780000.00,
  30000.00,
  1810000.00,
  'MOMO',
  'PENDING',
  'SHIPPING',
  '2026-05-01 09:00:00.000000',
  '2026-05-01 12:00:00.000000',
  NULL,
  NULL,
  '2026-05-01 08:30:00.000000',
  '2026-05-01 12:00:00.000000'
);

INSERT INTO `shop_order_item` (
  `id`, `order_id`, `product_id`, `product_name`, `unit_price`, `quantity`, `line_total`
) VALUES
  (1, 1, 1, 'Dumbbell Adjustable Pro', 1290000.00, 1, 1290000.00),
  (2, 1, 3, 'Premium Yoga Mat', 490000.00, 1, 490000.00);

ALTER TABLE `django_content_type` AUTO_INCREMENT = 13;
ALTER TABLE `auth_user` AUTO_INCREMENT = 2;
ALTER TABLE `shop_category` AUTO_INCREMENT = 4;
ALTER TABLE `shop_product` AUTO_INCREMENT = 7;
ALTER TABLE `shop_cart` AUTO_INCREMENT = 2;
ALTER TABLE `shop_order` AUTO_INCREMENT = 2;
ALTER TABLE `shop_order_item` AUTO_INCREMENT = 3;

SET FOREIGN_KEY_CHECKS = 1;