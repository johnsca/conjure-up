import yaml
from bundleplacer.assignmenttype import AssignmentType


class BundleWriter:

    def __init__(self, assignments, bundle):
        self.assignments = assignments
        self.bundle = bundle

    def _dict_for_service(self, svc, atype, to, services):

        tolist = []
        num_units = 1
        if svc.service_name in services:
            num_units = services[svc.service_name]['num_units'] + 1
            tolist = services[svc.service_name].get('to', [])

        d = dict(charm=svc.charm_source,
                 options=svc.options)
        if not svc.subordinate:
            d['num_units'] = num_units

        if to is not None:
            prefix = {AssignmentType.DEFAULT: "",
                      AssignmentType.BareMetal: "",
                      AssignmentType.KVM: "kvm:",
                      AssignmentType.LXD: "lxd:",
                      AssignmentType.LXC: "lxc:"}[atype]
            tolist.append("{}{}".format(prefix, to))

        if len(tolist) > 0:
            d['to'] = tolist
        return d

    def _dict_for_machine(self, mid):
        machine_tag = mid.split('/')[-2]
        cstr = "tags={}".format(machine_tag)
        return {"constraints": cstr}

    def _get_used_relations(self, services):
        relations = []
        service_names = [s.service_name for s in services]
        for svc in services:
            for src, dst in svc.relations:
                src_service = src.split(":")[0]
                dst_service = dst.split(":")[0]
                if src_service in service_names and \
                   dst_service in service_names:
                    relations.append([src, dst])
        # uniquify list of relations
        seen = set()
        return [r for r in relations
                if str(r) not in seen and not seen.add(str(r))]

    def write_bundle(self, filename):
        bundle = {}
        services = {}
        servicenames = []
        machines = self.bundle.machines
        iid_map = {}            # maps iid to juju machine number

        # get a machine dict for every machine with at least one
        # service
        existing_ids = list(machines.keys()) + ["_subordinates", "_default"]
        for mid in machines.keys():
            iid_map[mid] = mid

        for iid, d in self.assignments.items():
            if sum([len(svcs) for svcs in d.values()]) == 0:
                continue

            if iid not in existing_ids:
                machine_id = "{}".format(len(machines) + 1)
                iid_map[iid] = machine_id
                machines[machine_id] = self._dict_for_machine(iid)

        for iid, d in self.assignments.items():
            for atype, svcs in d.items():
                if len(svcs) < 1:
                    continue
                for svc in svcs:
                    sd = self._dict_for_service(svc, atype,
                                                iid_map.get(iid, None),
                                                services)
                    services[svc.service_name] = sd
                    servicenames.append(svc)

        bundle['machines'] = machines
        bundle['services'] = services
        bundle['relations'] = self._get_used_relations(servicenames)

        for k, v in self.bundle.extra_items().items():
            bundle[k] = v

        with open(filename, 'w') as f:
            yaml.dump(bundle, f, default_flow_style=False)
