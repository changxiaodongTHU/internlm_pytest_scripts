import pytest

import uniscale


class TestCaseActor:
    """
    Test for Actor API.
    """

    @pytest.mark.custom_cluster("./many_nodes.yaml")
    @pytest.mark.L3
    @pytest.mark.level(4)
    def test_actor_specify_node_001(self, env):
        # Test specfiy local node as ip
        print(f"--------,{env}")
        print(f'head node ip is:{env["head_node_addr"]}')
        # uniscale.init(server_address=env["head_node_addr"]+":10001")
        hostname_list = env["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            print(actor.metadata)
            actor.wait()
            print(actor.metadata)
            assert actor.metadata.node_ip == hostname
            uniscale.delete_actor(actor)

    @pytest.mark.custom_cluster("./many_nodes.yaml")
    @pytest.mark.L3
    @pytest.mark.level(2)
    def test_actor_specify_node_002(self, env):
        # Test specfiy local node as ip
        print(f"--------,{env}")
        print(f'head node ip is:{env["head_node_addr"]}')
        # uniscale.init(server_address=env["head_node_addr"]+":10001")
        hostname_list = env["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            print(actor.metadata)
            actor.wait()
            print(actor.metadata)
            assert actor.metadata.node_ip == hostname
            uniscale.delete_actor(actor)

    @pytest.mark.custom_cluster("./many_nodes2.yaml")
    @pytest.mark.L3
    @pytest.mark.level(3)
    def test_actor_specify_node_003(self, env):
        # Test specfiy local node as ip
        print(f"--------,{env}")
        print(f'head node ip is:{env["head_node_addr"]}')
        # uniscale.init(server_address=env["head_node_addr"]+":10001")
        hostname_list = env["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            print(actor.metadata)
            actor.wait()
            print(actor.metadata)
            assert actor.metadata.node_ip == hostname
            uniscale.delete_actor(actor)
