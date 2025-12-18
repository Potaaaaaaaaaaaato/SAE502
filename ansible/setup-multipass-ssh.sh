#!/bin/bash
set -e

echo "Configuration SSH pour Multipass..."

SSH_KEY_PATH="$HOME/.ssh/id_multipass_sae502"
VM_NAME="sae502-test"

if [ -f "$SSH_KEY_PATH" ]; then
    echo "Cle SSH existe deja"
else
    echo "Generation de la cle SSH..."
    ssh-keygen -t ed25519 -C "ansible-sae502" -f "$SSH_KEY_PATH" -N ""
    echo "Cle SSH generee"
fi

echo "Recuperation IP de la VM..."
VM_IP=$(multipass info $VM_NAME | grep IPv4 | awk '{print $2}')
echo "IP VM: $VM_IP"

echo "Copie de la cle publique dans la VM..."
cat "${SSH_KEY_PATH}.pub" | multipass exec $VM_NAME -- bash -c "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo "Cle copiee"

echo "Test de connexion SSH..."
if ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ubuntu@$VM_IP "echo 'OK'" 2>/dev/null; then
    echo "Connexion SSH OK"
else
    echo "ERREUR: Connexion SSH echouee"
    exit 1
fi

echo "Mise a jour inventaire Ansible..."
INVENTORY_FILE="inventories/multipass/hosts"
cp "$INVENTORY_FILE" "${INVENTORY_FILE}.backup" 2>/dev/null || true

cat > "$INVENTORY_FILE" << EOF
[multipass]
sae502-test ansible_host=$VM_IP ansible_user=ubuntu ansible_ssh_private_key_file=$SSH_KEY_PATH

[multipass:vars]
ansible_port=22
ansible_python_interpreter=/usr/bin/python3
ansible_ssh_common_args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
env_name=staging
domain_name=$VM_IP
enable_www_redirect=false
skip_ssl=true
EOF

echo "Inventaire mis a jour"

echo "Test connexion Ansible..."
if ansible multipass -i "$INVENTORY_FILE" -m ping; then
    echo ""
    echo "SUCCES - Ansible connecte a la VM"
    echo ""
    echo "Prochaines etapes:"
    echo "  ansible-playbook -i inventories/multipass/hosts playbooks/01-prepare-host.yml"
    echo "  ansible-playbook -i inventories/multipass/hosts playbooks/02-install-docker.yml"
    echo "  ansible-playbook -i inventories/multipass/hosts playbooks/03-deploy-application.yml --ask-vault-pass"
    echo ""
else
    echo "ERREUR: Connexion Ansible echouee"
    exit 1
fi
