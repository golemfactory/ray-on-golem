# golem-ray

## Interface

```
async with GolemNode() as golem:
    #   PaymentManager:
    #   *   Creates/recreates allocations
    #   *   Manages budget
    #   *   Accepts debit notes/invoices
    payment_manager = PaymentManager(golem)

    #   ActivityManager:
    #   *   On request creates/terminates activities
    #   *   Keeps internal state of a cluster and updates it:
    #       *   When activities are created/terminated
    #       *   When provider dies (--> checks activity state every 5s or so)
    #   *   Keeps cached demands, proposals etc to speed up activity creation
    #   *   Manages a Network object and adds all new activities to the network
    activity_manager = ActivityManager(golem)

    tasks = (
        asyncio.create_task(payment_manager.run()),
        asyncio.create_task(activity_manager.run()),
    )
    
    new_nodes = await activity_manager.add_nodes({"min_cpu": 2})
    print(new_nodes)
    #   [{some_id: {"ip": "192.168.0.2"}}]
    print(activity_manager.cluster_state)
    #  {{"nodes": { some_id: {"ip": "192.168.0.2"}}}, ...}

    await cluster_manager.terminate_nodes([some_id])
    print(activity_manager.cluster_state)
    #   {"nodes": {}}
```
