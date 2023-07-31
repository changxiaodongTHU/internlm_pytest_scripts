import pytest

import uniscale


class TestCaseActor:
    """
    Test for Actor API.
    """

    @pytest.mark.level(4)
    def test_actor_specify_node_002(self, default_cluster):
        # Test specfiy local node as ip
        # uniscale.init(server_address=connect["head_node_addr"]+":10001")
        hostname_list = default_cluster["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            actor.wait()
            assert actor.metadata.node_ip == hostname
            print(actor.metadata)
            uniscale.delete_actor(actor)

    @pytest.mark.level(2)
    def test_actor_specify_node_001(self, default_cluster):
        # Test specfiy local node as ip
        # uniscale.init(server_address=connect["head_node_addr"]+":10001")
        hostname_list = default_cluster["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            actor.wait()
            assert actor.metadata.node_ip == hostname
            print(actor.metadata)
            uniscale.delete_actor(actor)

    @pytest.mark.level(2)
    def test_actor_specify_node_003(self, default_cluster):
        # Test specfiy local node as ip
        # uniscale.init(server_address=connect["head_node_addr"]+":10001")
        hostname_list = default_cluster["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            actor.wait()
            assert actor.metadata.node_ip == hostname
            print(actor.metadata)
            uniscale.delete_actor(actor)

    @pytest.mark.level(3)
    def test_actor_specify_node_004(self, default_cluster):
        # Test specfiy local node as ip
        # uniscale.init(server_address=connect["head_node_addr"]+":10001")
        hostname_list = default_cluster["worker_node_addr"]
        # hostname_list=["10.140.0.135","10.140.0.165"]
        for hostname in hostname_list:
            print(f"The specified hostname: {hostname}")
            resource = uniscale.Resource(num_cpus=1, node_type=uniscale.NodeType.COMPUTE)
            actor = uniscale.new_actor(resource, node_name_or_ip=hostname)
            actor.wait()
            assert actor.metadata.node_ip == hostname
            print(actor.metadata)
            uniscale.delete_actor(actor)
