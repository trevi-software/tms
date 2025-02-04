# Copyright 2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
from collections import defaultdict

import requests

from odoo import SUPERUSER_ID, _, api, exceptions, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = ["project.task", "tms.analytic"]
    _name = "project.task"

    sale_line_id = fields.Many2one(index=True)
    sale_type_id = fields.Many2one(
        comodel_name="sale.order.type",
        related="sale_line_id.order_id.type_id",
        store=True,
    )
    shipping_origin_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Origin",
    )
    shipping_destination_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Destination",
    )
    trailer_requirement_ids = fields.Many2many(
        comodel_name="fleet.vehicle.tag",
        compute="_compute_trailer_requirement_ids",
        string="Trailer Req.",
        compute_sudo=True,
    )
    goods_id = fields.Many2one(
        comodel_name="tms.goods",
        string="Goods",
    )
    load_reference = fields.Char(string="Load Ref.")
    expedition = fields.Char()
    equipment_size_type_id = fields.Many2one(
        comodel_name="iso6346.size.type", string="Size Type", ondelete="restrict"
    )
    equipment_id = fields.Many2one(
        comodel_name="tms.equipment",
        string="Equipment",
    )
    seal = fields.Char()
    release_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Release",
    )
    release_locator = fields.Char()
    acceptance_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Aceptance",
    )
    acceptance_locator = fields.Char()
    wagon = fields.Char()
    vessel = fields.Char()
    booking_number = fields.Char()
    voyage_number = fields.Char()
    shipping_company_id = fields.Many2one(comodel_name="res.partner")
    # Destination port
    shipment_port_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Shipment Port",
    )
    # Origin port
    port_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Port",
    )
    loading_port_id = fields.Many2one(
        comodel_name="res.partner",
        string="Loading Port",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
    )
    unloading_port_id = fields.Many2one(
        comodel_name="res.partner",
        string="Unloading Port",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
    )
    final_destination_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_shipping_place", "=", True)],
        context={
            "default_is_shipping_place": True,
            "partner_show_only_name": True,
        },
        string="Port",
    )
    unload_service = fields.Boolean(string="Unload")
    distance_estimated = fields.Float(
        digits="TMS Distance",
    )
    distance_traveled = fields.Float(
        digits="TMS Distance",
    )
    odometer_start = fields.Float(
        digits="TMS Distance",
    )
    odometer_stop = fields.Float(
        digits="TMS Distance",
    )
    tms_package_ids = fields.Many2many(
        comodel_name="tms.package",
        relation="project_task_tms_package_rel",
        column1="project_task_id",
        column2="tms_package_id",
        string="Packages",
    )
    tms_package_all_ids = fields.Many2many(
        comodel_name="tms.package",
        compute="_compute_tms_package_all_ids",
        string="All Packages",
    )
    is_transport_order = fields.Boolean(
        compute="_compute_is_transport_order",
        store=True,
        string="Transport Order",
    )
    checkpoint_ids = fields.One2many(
        comodel_name="project.task.checkpoint",
        inverse_name="task_id",
    )
    stopped_time = fields.Float(
        compute="_compute_stopped_time",
        store=True,
    )
    free_stoped_time = fields.Float()
    volume = fields.Float(
        compute="_compute_package_totals",
        digits="TMS Volume",
    )
    weight = fields.Float(
        compute="_compute_package_totals",
        digits="TMS Weight",
    )
    number_of_packages = fields.Integer(
        compute="_compute_package_totals",
    )
    pallet_qty = fields.Integer(
        compute="_compute_package_totals",
        string="Pallets",
    )
    euro_pallet_qty = fields.Integer(
        compute="_compute_package_totals",
        string="Euro Pallets",
    )
    tractor_id = fields.Many2one(group_expand="_read_group_tractor_ids")
    force_origin = fields.Boolean()
    force_destination = fields.Boolean()
    progress_status = fields.Selection(
        [
            ("not_started", "Not started"),
            ("in_progress", "In progress"),
            ("closed", "Closed"),
        ],
        compute="_compute_progress_status",
        store=True,
    )
    pending_duration_estimated = fields.Float(
        compute="_compute_pending_duration_estimated", store=True
    )

    @api.depends("tms_package_ids", "child_ids")
    def _compute_tms_package_all_ids(self):
        for task in self:
            if task.child_ids:
                alltasks = task.search([("id", "child_of", [task.id])])
                tms_packages = alltasks.mapped("tms_package_ids")
            else:
                tms_packages = task.tms_package_ids
            task.tms_package_all_ids = tms_packages.sorted("sequence")

    @api.depends(
        "tms_package_ids.shipping_weight",
        "tms_package_ids.shipping_volume",
        "tms_package_ids.number_of_packages",
        "tms_package_ids.pallet_qty",
        "tms_package_ids.euro_pallet_qty",
    )
    def _compute_package_totals(self):
        for task in self:
            weight = volume = number_of_packages = 0.0
            pallet_qty = euro_pallet_qty = 0.0
            for package in task.tms_package_all_ids:
                weight += package.shipping_weight
                volume += package.shipping_volume
                number_of_packages += package.number_of_packages
                pallet_qty += package.pallet_qty
                euro_pallet_qty += package.euro_pallet_qty
            task.update(
                {
                    "weight": weight,
                    "volume": volume,
                    "number_of_packages": number_of_packages,
                    "pallet_qty": pallet_qty,
                    "euro_pallet_qty": euro_pallet_qty,
                }
            )

    @api.depends("tractor_id")
    def _compute_is_transport_order(self):
        for task in self:
            task.is_transport_order = bool(task.tractor_id)

    @api.depends("checkpoint_ids")
    def _compute_trailer_requirement_ids(self):
        for task in self.sudo():
            task.trailer_requirement_ids = task.checkpoint_ids.mapped(
                "place_id.trailer_tag_ids"
            )

    @api.depends("checkpoint_ids.stopped_time")
    def _compute_stopped_time(self):
        for task in self:
            task.stopped_time = sum(task.mapped("checkpoint_ids.stopped_time"))

    @api.depends("stage_id")
    def _compute_progress_status(self):
        for task in self:
            if task.stage_id.is_closed:
                task.progress_status = "closed"
            elif task.stage_id.sequence == 1:
                task.progress_status = "not_started"
            else:
                task.progress_status = "in_progress"

    @api.depends("progress_status", "checkpoint_ids.departure_time")
    def _compute_pending_duration_estimated(self):
        for task in self:
            if task.progress_status == "closed":
                task.pending_duration_estimated = 0.0
            else:
                task.pending_duration_estimated = sum(
                    task.checkpoint_ids.filtered(lambda c: not c.departure_time).mapped(
                        "duration_estimated"
                    )
                )

    @api.onchange("tractor_id")
    def _onchange_tractor_id_user(self):
        # Normally is only one user linked
        users = self.tractor_id.driver_id.user_ids
        if users:
            self.user_ids = [(6, 0, users.ids)]

    @api.onchange("user_ids")
    def _onchange_user_ids(self):
        partner_user = self.user_ids[0].partner_id
        if partner_user.is_driver:
            self.driver_id = partner_user

    @api.onchange("odometer_start", "odometer_stop")
    def _onchange_odometer(self):
        for task in self:
            if not task.odometer_stop:
                continue
            task.distance_traveled = task.odometer_stop - task.odometer_start

    @api.model
    def child_sync_field_list(self):
        return [
            "tractor_id",
            "trailer_id",
            "user_ids",
            "driver_id",
            "vendor_id",
        ]

    @api.model
    def sale_sync_field_list(self):
        return [
            "booking_number",
            "wagon",
            "vessel",
            "voyage_number",
            "release_id",
            "release_locator",
            "acceptance_id",
            "acceptance_locator",
            "shipping_company_id",
            "shipment_port_id",
            "port_id",
            "loading_port_id",
            "unloading_port_id",
            "final_destination_id",
            "unload_service",
        ]

    @api.model
    def sale_line_sync_field_list(self):
        sale_line_fields = list(self.env["tms.analytic"].analytic_fields())
        sale_line_fields.extend(
            [
                "shipping_origin_id",
                "shipping_destination_id",
                "tms_package_ids",
                "equipment_size_type_id",
                "equipment_id",
                "seal",
                "vendor_id",
            ]
        )
        return sale_line_fields

    def write_sale_fields(self, vals):
        if "write_from_so_line" in self.env.context or not any(
            x.sale_line_id for x in self
        ):
            return
        sale_lines = self.sudo().mapped("sale_line_id")
        sale_vals = {
            field: vals[field]
            for field in vals.keys()
            if field in self.sale_sync_field_list()
        }
        sale_line_vals = {
            field: vals[field]
            for field in vals.keys()
            if field in self.sale_line_sync_field_list()
        }
        if sale_vals:
            sale_lines.mapped("order_id").with_context(write_from_task=True).write(
                sale_vals
            )
        if sale_line_vals:
            sale_lines.with_context(write_from_task=True).write(sale_line_vals)

    def _check_incompatible_tags(self, vals):
        fleet_vehicle = self.env["fleet.vehicle"]
        if "tractor_id" in vals or "trailer_id" in vals:
            for task in self:
                if task.trailer_requirement_ids:
                    vehicles = fleet_vehicle.browse(
                        [vals.get("tractor_id", False), vals.get("trailer_id", False)]
                    )
                    tags = vehicles.mapped("tag_ids")
                    if not task.trailer_requirement_ids <= tags:
                        raise ValidationError(_("Incompatible equipment"))

    def write(self, vals):
        # Onchange values are not stored when drag and drop in kanban view
        force_onchange = (
            self.env.context.get("params", {}).get("view_type", "") == "kanban"
        )
        if force_onchange and "tractor_id" in vals:
            dummy_task = self.new({"tractor_id": vals["tractor_id"]})
            dummy_task._onchange_tractor_id()
            dummy_task._onchange_tractor_id_user()
            dummy_task._onchange_driver_id()
            new_vals = dummy_task._convert_to_write(dummy_task._cache)
            vals.pop("sale_line_id", None)
            vals.update(new_vals)
        elif force_onchange and "driver_id" in vals:
            dummy_task = self.new({"driver_id": vals["driver_id"]})
            dummy_task._onchange_driver_id()
            vals.update(dummy_task._convert_to_write(dummy_task._cache))
        if "parent_id" in vals:
            parent_task = self.browse(vals["parent_id"])
            for field in self.child_sync_field_list():
                vals[field] = parent_task._fields[field].convert_to_write(
                    parent_task[field], parent_task
                )
        self._check_incompatible_tags(vals)
        childs = self.mapped("child_ids")
        if childs:
            child_vals = {}
            for field in self.child_sync_field_list():
                if field in vals:
                    child_vals[field] = vals[field]
            if child_vals:
                vals["child_ids"] = [(1, x.id, child_vals) for x in childs]
        self.write_sale_fields(vals)
        return super().write(vals)

    @api.model
    def map_task2vehicle_fields(self):
        """Map equivalency between task and vehicle fields to pass filter domain"""
        return {"sale_type_id": "sale_type_ids"}

    @api.model
    def _read_group_tractor_ids(self, tractors, domain, order):
        if not self.env.context.get("tms_show_all_kanban_vehicles", False):
            return tractors
        search_domain = [
            "|",
            ("id", "in", tractors.ids),
            ("always_show_in_kanban", "=", True),
            ("vehicle_type", "=", "tractor"),
        ]
        if self.env.context.get("pass_task2vehicle_filter", False):
            # TODO: Use expression when fix https://github.com/odoo/odoo/issues/103214
            TRUE_DOMAIN = ("id", "!=", False)  # expression.TRUE_DOMAIN
            vehicle_domain = []
            task2vehicle_map = self.map_task2vehicle_fields()
            for t in domain:
                if not isinstance(t, (list, tuple)):
                    vehicle_domain.append(t)
                elif t[0] in task2vehicle_map.keys():
                    vehicle_field = task2vehicle_map[t[0]]
                    # Show vehicles with empty field too
                    vehicle_domain.extend(
                        ["|", (vehicle_field, t[1], t[2]), (vehicle_field, "=", False)]
                    )
                else:
                    vehicle_domain.append(TRUE_DOMAIN)
            search_domain = expression.AND([search_domain, vehicle_domain])

        tractor_ids = tractors._search(
            search_domain, order=order, access_rights_uid=SUPERUSER_ID
        )
        tractors = tractors.browse(tractor_ids)
        if "max_vehicle_tasks" in self.env.context:
            tractors = tractors.with_context(task_domain=domain).filtered(
                "is_available"
            )
        return tractors.sorted(key="task_pending_duration_estimated")

    def _all_places(self):
        places = self.release_id | self.shipping_origin_id
        if not self.force_origin:
            places |= self.child_ids.mapped("shipping_origin_id")
            places |= self.mapped("tms_package_all_ids.shipping_origin_id")
        if not self.force_destination:
            places |= self.mapped("tms_package_all_ids.shipping_destination_id")
            places |= self.child_ids.mapped("shipping_destination_id")
        places |= self.shipping_destination_id | self.acceptance_id
        return places

    def get_checkpoint_key(self, package, orig_dest):
        self.ensure_one()
        date = package.pickup_date or fields.datetime.max
        # Evaluate force_xx to set place from task instead of package
        place = (self if self["force_{}".format(orig_dest)] else package)[
            "shipping_{}_id".format(orig_dest)
        ]
        if orig_dest == "destination" and package.forecast_unload_date:
            date = package.forecast_unload_date
        # Group checkpoints in same calendar week
        return place, date.strftime("%Y%W"), orig_dest

    def _prepare_checkpoint_vals(self, key, packages, sequence):
        self.ensure_one()
        place = key[0]
        orig_dest = key[2]
        return {
            "place_id": place.id,
            "sequence": sequence,
            "automatic": True,
            "package_{}_ids".format(orig_dest): [(6, 0, packages)],
        }

    def fill_checkpoints(self):
        for task in self:
            task.checkpoint_ids.filtered("automatic").unlink()
            checkpoints_dic = defaultdict(list)
            for orig_dest in ("origin", "destination"):
                for package in task.tms_package_all_ids:
                    key = task.get_checkpoint_key(package, orig_dest)
                    if not key[0]:
                        continue
                    checkpoints_dic[key].append(package.id)
            checkpoint_vals_list = []
            seq = 0
            init_place = task.release_id or task.shipping_origin_id
            last_place = init_place
            for key, packages in sorted(
                checkpoints_dic.items(),
                key=lambda kv: (0 if kv[0][2] == "origin" else 1, kv[0][1]),
            ):
                # Add release_id or task origin as first checkpoint
                if init_place and seq == 0 and key[0] != init_place:
                    init_key = (init_place, None, "origin")
                    checkpoint_vals_list.append(
                        (0, 0, self._prepare_checkpoint_vals(init_key, [], seq))
                    )
                seq += 5
                checkpoint_vals_list.append(
                    (0, 0, self._prepare_checkpoint_vals(key, packages, seq))
                )
                last_place = key[0]
            # Add acceptance_id checkpoint or task destination as last checkpoint
            end_place = task.acceptance_id or task.shipping_destination_id
            if end_place and end_place != last_place:
                seq += 5
                key = (end_place, None, "destination")
                checkpoint_vals_list.append(
                    (0, 0, self._prepare_checkpoint_vals(key, [], seq))
                )
            task.checkpoint_ids = checkpoint_vals_list

    def open_in_webmap(self):
        points_list = []
        google_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_geolocalize.google_map_api_key")
        )
        for line in self.mapped("checkpoint_ids"):
            latitude = line.place_id.partner_latitude
            longitude = line.place_id.partner_longitude
            if latitude and longitude:
                points_list.append("%s,%s" % (latitude, longitude))
        url = "/tms/static/src/googlemaps/get_route.html?coords=%s&key=%s" % (
            ",".join(points_list),
            google_key,
        )
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "nodestroy": True,
            "target": "new",
        }

    def get_route_info(self):
        google_map_api_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_geolocalize.google_map_api_key")
        )
        if google_map_api_key:
            return self._get_route_googlemap()
        return self._get_route_openrouteservice()

    def _get_route_googlemap(self):
        google_key = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_geolocalize.google_map_api_key")
        )
        for task in self:
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            points_list = []
            for line in task.checkpoint_ids:
                latitude = line.place_id.partner_latitude
                longitude = line.place_id.partner_longitude
                if latitude and longitude:
                    points_list.append("%s,%s" % (latitude, longitude))
            params = {
                "origins": "|".join(points_list[:-1]),
                "destinations": "|".join(points_list[1:]),
                "mode": "driving",
                "language": self.env.lang,
                "sensor": "false",
            }
            if google_key:
                params.update({"key": google_key})
            try:
                # TODO: test after change simplejson to json
                result = json.loads(requests.get(url, params=params).content)
                total_distance = total_duration = 0.0
                if result["status"] != "OK":
                    task.update({"distance_estimated": 0.0, "planned_hours": 0.0})
                    return
                for i, checkpoint in enumerate(task.checkpoint_ids[1:]):
                    distance = (
                        result["rows"][i]["elements"][i]["distance"]["value"] / 1000.0
                    )
                    duration = (
                        result["rows"][i]["elements"][i]["duration"]["value"] / 3600.0
                    )
                    checkpoint.update(
                        {"distance_estimated": distance, "duration_estimated": duration}
                    )
                    total_distance += distance
                    total_duration += duration
                task.update(
                    {
                        "distance_estimated": total_distance,
                        "planned_hours": total_duration,
                    }
                )
            except Exception as err:
                raise exceptions.UserError(
                    _("Google Maps is not available: %s") % str(err)
                ) from err

    def _get_route_openrouteservice(self):
        # TODO: Change to company field
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("base_geolocalize.openrouteservice_api_key")
        )
        headers = {
            "Accept": "application/json, application/geo+json, "
            "application/gpx+xml, img/png; charset=utf-8",
            "Authorization": token,
            "Content-Type": "application/json; charset=utf-8",
        }
        url = "https://api.openrouteservice.org/v2/matrix/driving-hgv"
        for task in self:
            points_list = []
            for line in task.checkpoint_ids:
                latitude = line.place_id.partner_latitude
                longitude = line.place_id.partner_longitude
                if latitude and longitude:
                    points_list.append([longitude, latitude])
            body = {
                "locations": points_list,
                "destinations": list(range(1, len(points_list))),
                "id": str(task.id),
                "metrics": ["distance", "duration"],
                "units": "km",
            }
            response = requests.post(url, json=body, headers=headers)
            if response.status_code != 200:
                _logger.error(
                    "Request to openrouteservice failed.\nCode: %s\nContent: %s"
                    % (response.status_code, response.content)
                )
                task.update({"distance_estimated": 0.0, "planned_hours": 0.0})
                return
            result = response.json()
            total_distance = total_duration = 0.0
            for i, checkpoint in enumerate(task.checkpoint_ids[1:]):
                distance = result["distances"][i][i]
                duration = result["durations"][i][i] / 3600.0
                checkpoint.update(
                    {"distance_estimated": distance, "duration_estimated": duration}
                )
                total_distance += distance
                total_duration += duration
            task.update(
                {
                    "distance_estimated": total_distance,
                    "planned_hours": total_duration,
                }
            )
