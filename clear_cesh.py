def write(self, values):
        res = super(ResUsers, self).write(values)
        if 'pos_config_ids' in values:
            self.env['ir.model.access'].call_cache_clearing_methods()
            self.env['ir.rule'].clear_caches()
            self.has_group.clear_cache(self)
        return res